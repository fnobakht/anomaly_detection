# coding=utf-8
# @author: cer

import random
import numpy as np
from collections import defaultdict

flatten = lambda l: [item for sublist in l for item in sublist]  # 二维展成一维
index_seq2slot = lambda s, index2slot: [index2slot[i] for i in s]
index_seq2word = lambda s, index2word: [index2word[i] for i in s]


def data_pipeline(data, length=50):
    data = [t[:-1] for t in data]  # 去掉'\n'
    # 数据的一行像这样：'BOS i want to fly from baltimore to dallas round trip EOS
    # \tO O O O O O B-fromloc.city_name O B-toloc.city_name B-round_trip I-round_trip atis_flight'
    # 分割成这样[原始句子的词，标注的序列，intent]
    data = [[t.split("\t")[0].split(" "), t.split("\t")[1].split(" ")[:-1], t.split("\t")[1].split(" ")[-1]] for t in
            data]
    data = [[t[0][1:-1], t[1][1:], t[2]] for t in data]  # 将BOS和EOS去掉，并去掉对应标注序列中相应的标注
    for k in range(len(data)):
        if (len(data[k][2]) == 0):
            data[k][2] = 'atis_unsupported'
    # seq_in, seq_out, intent = list(zip(*data))
    seq_in, _, intent = list(zip(*data))
    sin = []
    # sout = []
    # padding，原始序列和标注序列结尾+<EOS>+n×<PAD>
    for i in range(len(seq_in)):
        temp = seq_in[i]
        if len(temp) < length:
            temp.append('<EOS>')
            while len(temp) < length:
                temp.append('<PAD>')
        else:
            temp = temp[:length]
            temp[-1] = '<EOS>'
        sin.append(temp)

        # temp = seq_out[i]
        # if len(temp) < length:
        #     while len(temp) < length:
        #         temp.append('<PAD>')
        # else:
        #     temp = temp[:length]
        #     temp[-1] = '<EOS>'
        # sout.append(temp)
        # data = list(zip(sin, sout, intent))
        data = list(zip(sin, intent))
    return data


def get_info_from_training_data(data):
    # seq_in, seq_out, intent = list(zip(*data))
    seq_in, intent = list(zip(*data))
    vocab = set(flatten(seq_in))
    # slot_tag = set(flatten(seq_out))
    intent_tag = set(intent)
    
    word2index = {'<PAD>': 0, '<UNK>': 1, '<SOS>': 2, '<EOS>': 3}
    for token in vocab:
        if token not in word2index.keys():
            word2index[token] = len(word2index)

    index2word = {v: k for k, v in word2index.items()}

    # tag2index = {'<PAD>': 0, '<UNK>': 1, "O": 2}
    # for tag in slot_tag:
    #     if tag not in tag2index.keys():
    #         tag2index[tag] = len(tag2index)
    # index2tag = {v: k for k, v in tag2index.items()}

    # intent2index
    intent2index = {'<UNK>': 0}
    for ii in intent_tag:
        if ii not in intent2index.keys():
            intent2index[ii] = len(intent2index)

    # 生成index2intent
    index2intent = {v: k for k, v in intent2index.items()}
    # return word2index, index2word, tag2index, index2tag, intent2index, index2intent
    return word2index, index2word, intent2index, index2intent


def getBatch(batch_size, train_data):
    random.shuffle(train_data)
    sindex = 0
    eindex = batch_size
    while eindex < len(train_data):
        batch = train_data[sindex:eindex]
        temp = eindex
        eindex = eindex + batch_size
        sindex = temp
        yield batch


# def to_index(train, word2index, slot2index, intent2index):
def to_index(train, word2index, intent2index):
    new_train = []
    # for sin, sout, intent in train:
    for sin, intent in train:
        sin_ix = list(map(lambda i: word2index[i] if i in word2index else word2index["<UNK>"],
                          sin))
        true_length = sin.index("<EOS>")
        # sout_ix = list(map(lambda i: slot2index[i] if i in slot2index else slot2index["<UNK>"], sout))
        intent_ix = intent2index[intent] if intent in intent2index else intent2index["<UNK>"]
        # new_train.append([sin_ix, true_length, sout_ix, intent_ix])
        # new_train.append([sin_ix, true_length, sout_ix, intent_ix])
        new_train.append([sin_ix, true_length, intent_ix])
    return new_train



def load_embedding_from_disks(glove_filename, with_indexes=True):
    """
    Read a GloVe txt file. If `with_indexes=True`, we return a tuple of two dictionnaries
    `(word_to_index_dict, index_to_embedding_array)`, otherwise we return only a direct 
    `word_to_embedding_dict` dictionnary mapping from a string to a numpy array.
    """
    if with_indexes:
        word_to_index_dict = dict()
        index_to_embedding_array = []
    else:
        word_to_embedding_dict = dict()

    
    with open(glove_filename, 'r', encoding="utf8") as glove_file:
        for (i, line) in enumerate(glove_file):
            
            split = line.split(' ')
            
            word = split[0]
            
            representation = split[1:]
            representation = np.array(
                [float(val) for val in representation]
            )
            
            if with_indexes:
                word_to_index_dict[word] = i
                index_to_embedding_array.append(representation)
            else:
                word_to_embedding_dict[word] = representation

    _WORD_NOT_FOUND = [0.0]* len(representation)  # Empty representation for unknown words.
    if with_indexes:
        _LAST_INDEX = i + 1
        word_to_index_dict = defaultdict(lambda: _LAST_INDEX, word_to_index_dict)
        index_to_embedding_array = np.array(index_to_embedding_array + [_WORD_NOT_FOUND])
        return word_to_index_dict, index_to_embedding_array
    else:
        word_to_embedding_dict = defaultdict(lambda: _WORD_NOT_FOUND)
        return word_to_embedding_dict    