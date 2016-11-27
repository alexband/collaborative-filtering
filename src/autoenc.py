#!/usr/bin/env python2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from keras.callbacks import TensorBoard
from keras.layers import Input, Dense, Dropout
from keras.models import Model
from keras.regularizers import l2
from keras.optimizers import Adadelta
from sklearn.model_selection import train_test_split

from data import postprocess, trainSet, preprocess, import_sequence

train_seq, val_seq = import_sequence()
total_samples, input_dim = train_seq.shape

encoding_dim = 512
epochs = 1
big_batch_size = 25600
batch_size = 50

def batch_gen(x_train, batch_size):
    n_batches = total_samples / batch_size
    i = 0
    while True:
        if i > n_batches: i = 0

        x_in = x_train[i * batch_size:min((i + 1) * batch_size, total_samples), :].toarray()
        x_test = x_train[i * batch_size + 1:min((i + 1) * batch_size + 1, total_samples), :].toarray()

        diff = len(x_in) - len(x_test)
        if diff: x_test = np.vstack((x_test, x_test[-diff:]))
        
        yield (x_in, x_test)
        i += 1

def stream_gen(batch_size=50):
    n_batches = len(train_seq) / batch_size
    i = 0

    while True:
        train_array = np.zeros((batch_size, input_dim), dtype=np.float32)
        curr_client = 0
        rating_lst = []

        if i > n_batches: i = 0
        left = batch_size

        while left:
            user, item, rating = train_seq.iloc[i]
            if user == curr_client:
                rating_lst.append((item, rating))
            else:  # changed clients
                if rating_lst:
                    for j in range(len(rating_lst)):
                        for (it, r) in rating_lst[:j]:
                            train_array[batch_size-left, it] = r
                        left -=1 
                    rating_lst = []
                curr_client = user
            i += 1

        yield train_array, train_array

def one_hot_encode(item, rating):
    v = np.zeros(input_dim, dtype=np.float32)
    v[item] = rating
    return v

def sequence_encode(seq):
    v = np.zeros(input_dim, dtype=np.float32)
    for (it, r) in seq:
        v[it] = r
    return v

class KerasBaseline(object):
    # Visualize with tensorboard --logdir=/tmp/autoencoder

    def __init__(self):
        # this is our input placeholder
        input_d = Input(shape=(input_dim,))
        # "encoded" is the encoded representation of the input
        encoded = Dense(encoding_dim, activation='tanh', W_regularizer=l2(0.01))(input_d)
        encoded = Dropout(0.2)(encoded)
        # "decoded" is the lossy reconstruction of the input
        decoded = Dense(input_dim, activation='tanh', W_regularizer=l2(0.01))(encoded)

        # this model maps an input to its reconstruction
        self.autoencoder = Model(input=input_d, output=decoded)
        self.autoencoder.compile(optimizer='adadelta',
                                 loss='mean_squared_error',
                                 metrics=['accuracy'])

        # this model maps an input to its encoded representation
        self.encoder = Model(input=input_d, output=encoded)

        # create a placeholder for an encoded (32-dimensional) input
        encoded_input = Input(shape=(encoding_dim,))
        # retrieve the last layer of the autoencoder model
        decoder_layer = self.autoencoder.layers[-1]
        # create the decoder model
        self.decoder = Model(input=encoded_input, output=decoder_layer(encoded_input))


    def fit_gen(self):
        self.autoencoder.fit_generator(generator=batch_gen(train_seq, batch_size),
                                       nb_epoch=epochs, samples_per_epoch=total_samples,
                                       callbacks=[TensorBoard(log_dir='/tmp/autoencoder')])

    def fit(self, x_train, x_train_recon, x_test, x_test_recon):
        self.autoencoder.fit(x_train, x_train_recon,
                             batch_size=batch_size,
                             shuffle=False,
                             validation_split=0.1,
                             validation_data=(x_test, x_test_recon),
                             nb_epoch=epochs,
                             callbacks=[TensorBoard(log_dir='/tmp/autoencoder')])

    def predict_generator(self):
        # encode and decode some ratings
        # note that we take them from the *test* set
        encoded_ratings = self.encoder.predict_generator(batch_gen(x_train, batch_size),
                                                         10 * batch_size)
        decoded_ratings = self.decoder.predict(encoded_ratings)
        return decoded_ratings

    def score(self, validation_set):
        # Test with and without history sequence
        errors = np.empty(len(validation_set), dtype=np.float32)
        for i, (seq, (item, rating)) in enumerate(validation_set):
            reconstruction = self.autoencoder.predict(sequence_encode(seq))
            errors[i] = (reconstruction[item] - rating) ** 2
        return np.sqrt(np.mean(errors))


autoenc = KerasBaseline()
autoenc.fit_gen()
score = autoenc.score(x_val)
