# -*- coding: utf8 -*-

import logging
# from settings import CLASS_LEVEL1
# import all the variables and classes in .py
from settings import VOCABULARY_SIZE
from settings import SAVE_DIR
from settings import TRAINING_INSTANCES
from settings import TRAIN_SET_PATH
import os
import sys
import pandas
import numpy

import math


def get_logger(name):
    '''
    set and return the logger modula,
    output: std
    '''
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    fh = logging.FileHandler(name)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


def latest_save_num():
    '''
    get the latest save num for the dir in save file
    '''
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
    # list all the files in save dir
    files = os.listdir(SAVE_DIR)
    maxno = -1
    # print(files)
    for f in files:
        if os.path.isdir(SAVE_DIR + '/' + f):
            # print(f,'true')
            try:
                # print(name)
                no = int(f)
                maxno = max(maxno, no)
                # print(maxno)
            except Exception as e:
                print(e.message, file=sys.stderr)
                pass
    return maxno


class DataManager():
    '''
    data loading module
    '''
    # __df = None # not use this format of data initialization,
    # possible confusion
    # __cursor = 0

    def __init__(
            self,
            param_batch_size,
            param_training_instances_size):

        # param_topic_sentiment_count,
        # param_sentiment_count ):
        # self.df=None
        # self.cursor=0
        # self.batch_size=batch_size

        # global private variable initialized here

        # dataframe read by a chunk
        self.__current_dataframe_of_pandas = None
        # the cursor shifted in pandas,
        # it's the global cursor shift in dataframe
        self.__current_cursor_in_dataframe = 0
        self.__batch_size = param_batch_size
        # self.__topic_sentiment_count = param_topic_sentiment_count
        # self.__sentiment_count = param_sentiment_count
        self.__training_instances_size = param_training_instances_size

        # self.__batch_size = param_batch_size
        # the current cursor in file, is the line num
        # self.__current_cursor = 0
        # list_all_tweets_of_auser#the current file pointer
        # self.__current_file_pointer = None
        return None

    def load_dataframe_from_file(self, param_filepath_in):
        '''
        read once, initialize dataframe_of_pandas
        '''

        print('Loading dataframe...')
        self.__current_dataframe_of_pandas = pandas.read_csv(
            param_filepath_in, dtype=numpy.uint16, header=None,
            encoding='utf-8', sep='\s+', engine='c', low_memory=True)

        # self.__dataframe_of_pandas = \
        # pandas.read_csv(
        #     param_filepath_in, header = None,
        #     encoding = 'utf8',sep = '\t' , engine = 'c')
        # you can use regular expression in sep by setting engine = 'python'
        # engine = 'c' will face error,
        # 'c' requires all the data type to be the same

        # c do not support \t\n
        # print(len(self.__dataframe_of_pandas) )
        # currently every 9 lines describe a user
        return None

    def reshuffle_dataframe(self):
        self.__current_dataframe_of_pandas.sample(frac=1)

    def next_batch(self):
        '''
        obtain next batch
        possible out of range, you have to control the tail
        the best way is to call next_batch dataframe_size()//batch_size times
        then call tail_batch
        use reshape
        '''

        batch_size = self.__batch_size
        # start cursor
        s = self.__current_cursor_in_dataframe
        # end cursor
        t = s + batch_size
        # get the current chunk, chunk is a default dataframe,
        # should be transformed to float32,
        # or the dataformat will not be the same
        # dataframe_of_pandas = pandas.DataFrame(
        #     data=self.__chunks_of_pandas.get_chunk( chunk_size),
        #     dtype=numpy.float32)

        batch_index = s // batch_size

        print("Loading batch: %d" % (batch_index))
        # get the current chunk,
        # chunk is a default dataframe,
        # should be transformed to float32,
        # or the dataformat will not be the same
        # dataframe_of_pandas = self.__current_dataframe_of_pandas
        # .get_chunk(chunk_size)

        # print('get_chunk: ' + str( s//batch_size))

        batch_xn = numpy.zeros((batch_size,
                                VOCABULARY_SIZE),
                               dtype=numpy.int32)

        batch_wc = numpy.zeros((batch_size,
                                VOCABULARY_SIZE),
                               dtype=numpy.int32)

        for instance_i in range(s, t):
            # print('user_i: ' + str(user_i))
            # each user's time serial

            # one col for label
            pivot_wordindex = \
                self.__current_dataframe_of_pandas.iloc[instance_i][0]
            batch_xn[instance_i % batch_size][pivot_wordindex] = 1
            wc_values = \
                self.__current_dataframe_of_pandas.iloc[instance_i][1:].values
            for context_wordindex in wc_values:
                batch_wc[instance_i % batch_size][context_wordindex] += 1

            # print( label_shift)

            # batch_x[ user_i%batch_size] = \
            #     numpy.reshape(
            #         dataframe_of_pandas.iloc[user_i% batch_size][
            #             label_shift: ],
            #         (1+USER_TWITTER_COUNT+NEIGHBOR_TWITTER_COUNT,
            #          1+USER_TWITTER_COUNT+NEIGHBOR_TWITTER_COUNT,
            #          TWITTER_LENGTH, WORD_EMBEDDING_DIMENSION) )
            # batch_x[ user_i%batch_size] = \
            #     dataframe_of_pandas.iloc[
            #         user_i % batch_size][label_shift:].values.reshape(
            #             (1+USER_TWITTER_COUNT+NEIGHBOR_TWITTER_COUNT,
            #              1+USER_TWITTER_COUNT+NEIGHBOR_TWITTER_COUNT,
            #              TWITTER_LENGTH, WORD_EMBEDDING_DIMENSION))

            # dataframe_of_pandas infact is a dataframe of a chunk_size

            # print(batch_x.shape)

            # list_labels = self.__dataframe_of_pandas.iloc[ user_i , 0 ]
            # batch_y[ user_i%batch_size ][ 0 ] = list_labels[ 0 ]
            # batch_y[ user_i%batch_size ][ 1 ] = list_labels[ 1 ]

        self.__current_cursor_in_dataframe = t

        return batch_xn, batch_wc

    def set_current_cursor_in_dataframe_zero(self):
        '''
        if INSTANCE % batch_size == 0,
        then the tail_batch won't be called,
        so call this function to reset the
        __cursor_in_current_frame
        '''
        self.__current_cursor_in_dataframe = 0

    def tail_batch(self):
        '''
        if INSTANCE % batch_size != 0
        then call the tail_batch, padding the tail
        '''

        batch_size = self.__batch_size

        s = self.__current_cursor_in_dataframe
        t = s + batch_size

        batch_index = s // batch_size

        print("Loading batch: %d" % (batch_index))

        # self.__current_dataframe_of_pandas
        # get the current chunk,
        # chunk is a default dataframe,
        # should be transformed to float32,
        # or the dataformat will not be the same
        # .get_chunk(chunk_size)

        batch_xn = numpy.zeros((batch_size,
                                VOCABULARY_SIZE),
                               dtype=numpy.int32)

        batch_wc = numpy.zeros((batch_size,
                                VOCABULARY_SIZE),
                               dtype=numpy.int32)
        # complement the last chunk with the initial last chunk
        # assert len(self.__current_dataframe_of_pandas) == \
        # self.__training_instances_size
        last_batch_size = len(self.__current_dataframe_of_pandas)\
            % batch_size

        # append_times = batch_size // last_batch_size
        # append_tail = batch_size % last_batch_size

        # dataframe_of_pandas_compensated = \
        # pandas.DataFrame(data=None,
        #     columns=dataframe_of_pandas.axes[1])

        # for i in range(0, append_times):
        #     dataframe_of_pandas_compensated = \
        #         dataframe_of_pandas_compensated.append(
        #             dataframe_of_pandas.iloc[s:s + last_batch_size],
        #             ignore_index=True)
        # for ignore_index refer to the manual

        # dataframe_of_pandas_compensated = \
        # dataframe_of_pandas_compensated.append(
        #     dataframe_of_pandas.iloc[
        #         s: s + append_tail], ignore_index=True)

        for instance_i in range(s, t):
            # list_all_tweets_of_auser = \
            #     self.__dataframe_of_pandas.iloc[
            #       i,
            #       2:(2+1+USER_TWITTER_COUNT+NEIGHBOR_TWITTER_COUNT)].values.tolist()
            # list_a            label_shift = 1 #one col for label

            # batch_x[ user_i%batch_size] = \
            #     dataframe_of_pandas.iloc[
            #         user_i%batch_size][label_shift:].reshape((
            #               1+USER_TWITTER_COUNT+NEIGHBOR_TWITTER_COUNT,
            #               1+USER_TWITTER_COUNT+NEIGHBOR_TWITTER_COUNT,
            #               TWITTER_LENGTH, WORD_EMBEDDING_DIMENSION) )

            if (instance_i % batch_size) < last_batch_size:
                pivot_wordindex = \
                    self.__current_dataframe_of_pandas.iloc[
                        instance_i][0]

                batch_xn[instance_i % batch_size][pivot_wordindex] = 1
                wc_values = \
                    self.__current_dataframe_of_pandas.iloc[
                        instance_i][1:].values
                for context_wordindex in wc_values:
                    batch_wc[instance_i % batch_size][context_wordindex] += 1
            else:
                shift_in_last_batch_size = \
                    (instance_i % batch_size) % last_batch_size
                iloc_index = instance_i - instance_i % batch_size\
                    + shift_in_last_batch_size
                batch_xn[instance_i % batch_size] = \
                    self.__current_dataframe_of_pandas.iloc[
                        iloc_index][0]

                wc_values = \
                    self.__current_dataframe_of_pandas.iloc[
                        iloc_index][1:].values

                for context_wordindex in wc_values:
                    batch_wc[instance_i % batch_size][context_wordindex] += 1

        self.__current_cursor_in_dataframe = 0

        return batch_xn, batch_wc

    def tail_batch_nobatchpadding(self):
        batch_size = self.__batch_size

        s = self.__current_cursor_in_dataframe

        batch_index = s // batch_size

        print("Loading batch: %d" % (batch_index))

        # complement the last chunk with the initial last chunk
        # assert len(self.__current_dataframe_of_pandas) == \
        # self.__training_instances_size
        last_batch_size = len(self.__current_dataframe_of_pandas)\
            % batch_size
        t = s + last_batch_size

        batch_xn = numpy.zeros((last_batch_size,
                                VOCABULARY_SIZE),
                               dtype=numpy.int32)

        batch_wc = numpy.zeros((last_batch_size,
                                VOCABULARY_SIZE),
                               dtype=numpy.int32)

        for instance_i in range(s, t):
            # if 0 is a word, then 0 is calculated into the probability
            pivot_wordindex = \
                self.__current_dataframe_of_pandas.iloc[instance_i][0]
            batch_xn[instance_i % batch_size][pivot_wordindex] = 1
            wc_values = \
                self.__current_dataframe_of_pandas.iloc[instance_i][1:].values
            for context_wordindex in wc_values:
                batch_wc[instance_i % batch_size][context_wordindex] += 1

        self.__current_cursor_in_dataframe = 0

        return batch_xn, batch_wc

    def n_batches(self):
        # if self.__current_dataframe_of_pandas == None:
        #     print('Error: __current_dataframe_of_pandas == None',
        #         file=sys.stderr)
        # else:
        return math.ceil(
            self.__training_instances_size / self.__batch_size)


if __name__ == '__main__':
    # arr = numpy.array(1)
    # print(arr.shape) # = ()

    # oDataManager = DataManager(
    #     param_batch_size=2,
    #     param_training_instances_size=2)

    # oDataManager.load_dataframe_from_file('dataframetest.csv')
    # # print('----------getcwd()', os.getcwd())
    oDataManager = DataManager(
        param_batch_size=128,
        param_training_instances_size=TRAINING_INSTANCES)

    # # oDataManager.generate_csv_from_wordembbed( TRAIN_SET_PATH )

    oDataManager.load_dataframe_from_file(TRAIN_SET_PATH)

    # print(oDataManager.dataframe_size() // 64 )
    # print(oDataManager.dataeframe_size() % 64 )

    print('Hello')
    for i in range(0, TRAINING_INSTANCES // 1024):
        print(i)
        (batch_xn, batch_wc) = oDataManager.next_batch()
        print('----------shape_xn:',
              batch_xn.shape,
              '----------shape_wc:',
              batch_wc.shape)
    if TRAINING_INSTANCES % 1024 == 0:
        oDataManager.set_current_cursor_in_dataframe_zero()
    else:
        (batch_xn, batch_wc) = oDataManager.tail_batch()
        # size of torch in numpy
        print(batch_xn.shape)
        print(batch_wc.shape)
