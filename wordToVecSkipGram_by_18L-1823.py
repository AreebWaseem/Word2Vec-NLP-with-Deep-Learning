

import numpy as np
import re
from collections import defaultdict
import os.path
import sys


# --- CONSTANTS ----------------------------------------------------------------+


class word2vec():
    
    def __init__(self):
        
        self.n = settings['n']
        
        self.eta = settings['learning_rate']
        
        self.epochs = settings['epochs']
        
        self.window = settings['window_size']
        
        self.neg_sample_size = settings['neg_samp']
        
        self.total_word_count = 0
        pass

    # GENERATE TRAINING DATA
    def generate_training_data(self, settings, corpus):

        # GENERATE WORD COUNTS
        word_counts = defaultdict(int)
        for row in corpus:
            for word in row:
                
                self.total_word_count += 1
                word_counts[word] += 1

        self.v_count = len(word_counts.keys())

        # GENERATE LOOKUP DICTIONARIES
        self.words_list = sorted(list(word_counts.keys()), reverse=False)
        self.word_index = dict((word, i) for i, word in enumerate(self.words_list))
        self.index_word = dict((i, word) for i, word in enumerate(self.words_list))
        
        
        reversed_keys = sorted(word_counts, key= word_counts.get, reverse=True)
        
        #print(reversed_keys)

        training_data = []
        # CYCLE THROUGH EACH SENTENCE IN CORPUS
        for sentence in corpus:
            sent_len = len(sentence)

            # CYCLE THROUGH EACH WORD IN SENTENCE
            for i, word in enumerate(sentence):

                # w_target  = sentence[i]
                w_target = self.word2onehot(sentence[i])

                # CYCLE THROUGH CONTEXT WINDOW
                w_context = []
                w_negative_samples = []
                
                for j in range(i - self.window, i + self.window + 1):
                    if j != i and j <= sent_len - 1 and j >= 0:
                        w_context.append(self.word2onehot(sentence[j]))
                    
                cur_count = 0
                
                for reversed_key in reversed_keys:
                    
                    if(cur_count == self.neg_sample_size):
                        
                        break
                    
                    if(reversed_key is not word):
                        
                        w_negative_samples.append(self.word2onehot(reversed_key))
                        
                        cur_count += 1
                        
                    
                    
                    
                training_data.append([w_target, w_context, w_negative_samples])
                
        return np.array(training_data)

    # SOFTMAX ACTIVATION FUNCTION
    def softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)

    # CONVERT WORD TO ONE HOT ENCODING
    def word2onehot(self, word):
        word_vec = [0 for i in range(0, self.v_count)]
        word_index = self.word_index[word]
        word_vec[word_index] = 1
        return word_vec

    # FORWARD PASS
    def forward_pass(self, x):
        h = np.dot(self.w1.T, x)
        u = np.dot(self.w2.T, h)
        y_c = self.softmax(u)
        return y_c, h, u

    # BACKPROPAGATION
    def backprop(self, e, h, x, label):
        
        e_new = e + float(label)
      #  print('e',e)
       # print('e_new',e_new)
        dl_dw2 = np.outer(h, e_new)
        dl_dw1 = np.outer(x, np.dot(self.w2, e_new.T))

        # UPDATE WEIGHTS
        self.w1 = self.w1 - (self.eta * dl_dw1)
        self.w2 = self.w2 - (self.eta * dl_dw2)
        
        pass


    # TRAIN W2V model
    def train(self, training_data):
        # INITIALIZE WEIGHT MATRICES
        self.w1 = np.random.uniform(-0.8, 0.8, (self.v_count, self.n))  # embedding matrix
        self.w2 = np.random.uniform(-0.8, 0.8, (self.n, self.v_count))  # context matrix
        
        # CYCLE THROUGH EACH EPOCH
        for i in range(0, self.epochs):

            self.loss = 0

            # CYCLE THROUGH EACH TRAINING SAMPLE
            for w_t, w_c, w_neg in training_data:
                # FORWARD PASS
                y_pred, h, u = self.forward_pass(w_t)

                # CALCULATE ERROR
                    
                EI = np.sum([np.subtract(y_pred, word) for word in w_c], axis=0)
                
              

                # BACKPROPAGATION
                self.backprop(EI, h, w_t, float(0.0))
                
                # now for negative samples
                
                EI_neg = np.sum([np.subtract(y_pred, word) for word in w_neg], axis=0)
                
                #print(EI_neg)
                
               # print('EI two',EI_neg)
                
                self.backprop(EI_neg, h, w_t, float(-1.0))   

                # CALCULATE LOSS
                #self.loss += -np.sum([u[word.index(1)] for word in w_c]) + len(w_c) * np.log(np.sum(np.exp(u)))
                # self.loss += -2*np.log(len(w_c)) -np.sum([u[word.index(1)] for word in w_c]) + (len(w_c) * np.log(np.sum(np.exp(u))))

            print
            'EPOCH:', i, 'LOSS:', self.loss
        pass

    # input a word, returns a vector (if available)
    def word_vec(self, word):
        w_index = self.word_index[word]
        v_w = self.w1[w_index]
        return v_w

    # input a vector, returns nearest word(s)
    def vec_sim(self, vec, top_n):

        # CYCLE THROUGH VOCAB
        word_sim = {}
        
        for i in range(self.v_count):
            v_w2 = self.w1[i]
            theta_num = np.dot(vec, v_w2)
            theta_den = np.linalg.norm(vec) * np.linalg.norm(v_w2)
            theta = theta_num / theta_den

            word = self.index_word[i]
            word_sim[word] = theta

        words_sorted = sorted(word_sim.items(), key=lambda word, sim: sim, reverse=True)

        for word, sim in words_sorted[:top_n]:
            print
            word, sim

        pass

    # input word, returns top [n] most similar words
    def word_sim(self, word, top_n):

        w1_index = self.word_index[word]
        v_w1 = self.w1[w1_index]

        # CYCLE THROUGH VOCAB
        word_sim = {}
        for i in range(self.v_count):
            v_w2 = self.w1[i]
            theta_num = np.dot(v_w1, v_w2)
            theta_den = np.linalg.norm(v_w1) * np.linalg.norm(v_w2)
            theta = theta_num / theta_den

            word = self.index_word[i]
            word_sim[word] = theta
         #   print(word, theta)

        words_sorted = sorted(word_sim.items(),  key=lambda x: x[1], reverse=True)

        for word, sim in words_sorted[:top_n]:
            print (word, sim)

        pass
  
        
    
  




# --- EXAMPLE RUN --------------------------------------------------------------+
    

def readFileToCorpus(f):
    
    if os.path.isfile(f):
        file = open(f, "r") 
        i = 0
        corpus = [] 
        print("Reading file ", f)
        for line in file:
            i += 1
            sentence = line.split()
          
            corpus.append(sentence)
            if i % 1000 == 0:
      
                sys.stderr.write("Reading sentence " + str(i) + "\n")
    
        return corpus
    else:
       
        print("Error: corpus file ", f, " does not exist")
        sys.exit() 

settings = {}
settings['n'] = 5  # dimension of word embeddings
settings['window_size'] = 2  # context window +/- center word
settings['min_count'] = 0  # minimum word count
settings['epochs'] = 5000  # number of training epochs
settings['neg_samp'] = 10  # number of negative words to use during training
settings['learning_rate'] = 0.00001  # learning rate
np.random.seed(0)  # set the seed for reproducibility





corpus = readFileToCorpus('train.txt')


mini_corpus = corpus[1:1000]



# I have done negative sampling in generate training data and Back propogation for Negative and positive samples in train function


# INITIALIZE W2V MODEL
w2v = word2vec()

# generate training data
training_data = w2v.generate_training_data(settings, corpus)


# train word2vec model
w2v.train(training_data)

print(w2v.word_vec('the'))

print(w2v.word_sim('the',5))



