import graphlab as gl
import data_preprocess as dp
from graphlab.toolkits.cross_validation import KFold
from graphlab.toolkits.model_parameter_search import grid_search
import nlp_funcs as nl
from collections import Counter
import pandas as pd
import cPickle as pk

def load_everything():
    '''
    loads the dataframe of reviews data, removes 'Anonymous' reviews
    and drops columns we don't need for the recommender engine
    '''

    df = dp.load_data()
    # drop everything but user, product, rating
    df.drop(['date', 'time', 'review'], axis=1, inplace=True)
    # remove user 'Anonymous' -- necessary to match up size of products from
    # data_preprocess get users and products func
    df_no_anon = df[df['user'] != 'Anonymous']

    return df_no_anon

def train_engine(df, num_factors=20):
    '''
    trains recommendation engine on supplied dataframe with 'user' and 'review'
    columns
    returns engine for later use
    '''
    data = gl.SFrame(df)
    num_factors = 20
    rec_engine = gl.factorization_recommender.create(observation_data=data,
                                                     user_id="user",
                                                     item_id="product",
                                                     target='rating',
                                                     solver='auto',
                                                     num_factors=num_factors
                                                     )
    return rec_engine

def get_latent_feature_groups(rec_engine, df=None):
    '''
    breaks up users and products into groups based on latent features from the
    recommendation engine

    args:
    df -- dataframe with 'user', 'review', and 'product' columns
    * note the 'review' column is not in the df from load_everything()
    rec_engine -- graphlab recommendation factorizer engine
    returns:
    dictionary of groups of products with latent features
    '''
    # assign groups to users and products based on highest coefficient in the matrices
    if df is None:
        df = dp.load_data()

    d = rec_engine.get("coefficients")
    U1 = d['user']
    U2 = d['product']
    U1 = U1['factors'].to_numpy()
    U2 = U2['factors'].to_numpy()

    user_groups = U1.argmax(axis=1)
    prod_groups = U2.argmax(axis=1)

    users, products = dp.get_users_and_products(df)

    prod_group_dict = {}
    prod_group_dfs = {}
    for i in range(U1.shape[1]):
        # this gets the product names in each group
        prod_list = products[prod_groups == i].index
        prod_group_dict[i] = prod_list
        prod_list = set(prod_list)
        # this will get dataframes from the main df with products in each group
        prod_group_dfs[i] = df[df['product'].isin(prod_list)]

    return prod_group_dfs

def get_top_words(prod_group_dfs, num_words=50):
    '''
    gets top words for each product group and returns them in a dictionary

    args:
    prod_group_dfs -- dict of product groups
    num_words -- number of words per product group to return

    returns:
    top_words_
    '''
    top_words = {}
    top_words_set = set()
    word_list = []
    for i in range(len(prod_group_dfs.keys())):
        words = nl.get_top_words_lemmatize(prod_group_dfs[i], num_words)
        top_words_set = top_words_set | set(words)
        top_words[i] = words
        word_list.extend(words)

    word_counter = Counter(word_list)
    return top_words, word_counter

def get_top_ngrams(prod_group_dfs, num_words=50, ngram_range=(2, 2)):
    '''
    gets top words for each product group and returns them in a dictionary

    args:
    prod_group_dfs -- dict of product groups
    num_words -- number of words per product group to return

    returns:
    top_words_
    '''
    top_words = {}
    top_words_set = set()
    word_list = []
    for i in range(len(prod_group_dfs.keys())):
        words = nl.get_top_words_lemmatize(prod_group_dfs[i], 50, ngram_range=ngram_range)
        top_words_set = top_words_set | set(words)
        top_words[i] = words
        word_list.extend(words)

    word_counter = Counter(word_list)
    return top_words, word_counter

def save_engine(rec_engine, filename='leafly/20groupsrec_engine.model'):
    '''
    saves recommendation engine for later use
    '''
    rec_engine.save(filename)

def load_engine(filename='leafly/20groupsrec_engine.model'):
    return gl.load_model(filename)

def pickle_top_words(top_words, filename='leafly/top_words.pk'):
    '''
    pickles to disk the top_words dictionary for product latent groups

    args:
    top_words -- dictionary of top_words by tfidf for each product group

    returns:
    1 if successful, 0 otherwise
    '''
    try:
        pk.dump(top_words, open(filename, 'w'), 2)
        return 1
    except Exception as e:
        print 'Error pickling:', e
        return 0

if __name__ == "__main__":
    df = load_everything()
    #rec_engine = train_engine(df)
    rec_engine = load_engine()
    prod_group_dfs = get_latent_feature_groups(rec_engine)
    top_words, word_counter = get_top_words(prod_group_dfs, 100)
    #top_bigrams, bigram_counter = get_top_ngrams(prod_group_dfs)
