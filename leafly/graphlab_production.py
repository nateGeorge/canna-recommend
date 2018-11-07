import graphlab as gl
import leafly.data_preprocess as dp
from graphlab.toolkits.cross_validation import KFold
from graphlab.toolkits.model_parameter_search import grid_search
import leafly.nlp_funcs as nl
import leafly.scrape_leafly as sl
from collections import Counter
import pandas as pd
import pickle as pk
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import collections
import os

def load_everything(drop=True, anon=False):
    '''
    loads the dataframe of reviews data, removes 'Anonymous' reviews
    and drops columns we don't need for the recommender engine

    args:
    drop -- whether or not to drop non-critical columns
    anon -- whether to keep anonymous reviews or not
    '''

    df = dp.load_data()
    # drop everything but user, product, rating
    if drop:
        df.drop(['date', 'time', 'review'], axis=1, inplace=True)
    # remove user 'Anonymous' -- necessary to match up size of products from
    # data_preprocess get users and products func
    if not anon:
        df_no_anon = df[df['user'] != 'Anonymous']

    return df_no_anon

def train_engine(df, num_factors=10, max_iterations=50):
    '''
    found 10 to be a suitable number from gridsearching
    trains recommendation engine on supplied dataframe with 'user' and 'review'
    columns
    returns engine for later use
    '''
    data = gl.SFrame(df)
    rec_engine = gl.factorization_recommender.create(observation_data=data,
                                                     user_id="user",
                                                     item_id="product",
                                                     target='rating',
                                                     solver='auto',
                                                     num_factors=num_factors,
                                                     max_iterations=max_iterations
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
    # assign groups to users and products based on highest coefficient in the
    # matrices
    if df is None:
        df = dp.load_data()

    d = rec_engine.get("coefficients")
    U1 = d['user']
    U2 = d['product']
    U1 = U1['factors'].to_numpy()
    U2 = U2['factors'].to_numpy()

    user_groups = U1.argmax(axis=1)
    prod_groups = U2.argmax(axis=1)

    pk.dump(U1, open('user_latent_matrix.pk', 'w'), 2)
    pk.dump(U2, open('product_latent_matrix.pk', 'w'), 2)

    pk.dump(user_groups, open('user_groups.pk', 'w'), 2)
    pk.dump(prod_groups, open('product_groups.pk', 'w'), 2)

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

    user_group_dict = {}
    user_group_dfs = {}
    for i in range(U1.shape[1]):
        # this gets the product names in each group
        user_list = users[user_groups == i].index
        user_group_dict[i] = user_list
        user_list = set(user_list)
        # this will get dataframes from the main df with products in each group
        user_group_dfs[i] = df[df['user'].isin(user_list)]

    return prod_group_dfs, user_group_dfs


def get_top_words(group_dfs, num_words=200):
    '''
    gets top words for each product group and returns them in a dictionary

    args:
    group_dfs -- dict of product or user groups
    num_words -- number of words per product group to return

    returns:
    top_words -- dict of dicts (numbers ranging in number of groups)
    with words as keys and tfidf vector values as values
    '''
    all_review_vects = {}
    top_words = {}
    top_vects = {}
    top_words_set = set()
    word_list = []
    for i in range(len(list(group_dfs.keys()))):
        words, vects, review_vects = nl.get_top_words_lemmatize(
            group_dfs[i])  # , num_words)
        all_review_vects[i] = review_vects
        top_words_set = top_words_set | set(words)
        top_words[i] = {}
        for j, w in enumerate(words):
            top_words[i][w] = vects[j]

        word_list.extend(words)

    word_counter = Counter(word_list)
    return top_words, word_counter


def get_top_ngrams(group_dfs, num_words=200, ngram_range=(2, 2)):
    '''
    gets top words for each product group and returns them in a dictionary

    args:
    group_dfs -- dict of product or user groups
    num_words -- number of words per product group to return

    returns:
    top_words_
    '''
    top_words = {}
    top_words_set = set()
    word_list = []
    for i in range(len(list(prod_group_dfs.keys()))):
        words, vects = nl.get_top_words_lemmatize(
            group_dfs[i], 50, ngram_range=ngram_range)
        top_words_set = top_words_set | set(words)
        top_words[i] = words
        word_list.extend(words)

    word_counter = Counter(word_list)
    return top_words, word_counter


def save_engine(rec_engine, filename='leafly/10groupsrec_engine.model'):
    '''
    saves recommendation engine for later use
    '''
    rec_engine.save(filename)


def load_engine(filename='leafly/10groupsrec_engine.model'):
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
        print('Error pickling:', e)
        return 0


def get_rec_based_on_words(words, group='user'):
    '''
    gets recommendation of top products for a user or product group based on
    list of words

    args:
    words -- list of words to use for recommendation
    group -- either 'product' or 'user', which group the words are meant to
    be compared with
    '''
    pass


def write_top_words(words, filename):
    '''
    takes list of words and writes to file
    '''
    with open(filename, 'w') as f:
        for w in words:
            f.writeline('w')


def get_prod_similarity(words, top_words):
    '''
    gets tfidf similarity of words vectorized into tfidf and prod group
    words

    args:
    words -- list of words chosen by user
    prod_top_words -- dict of words: vector value from get_top_words

    returns:
    ordered list of products, descending by similarity
    '''
    sims = {}
    for p in top_words:
        sims[p] = 0
        for w in words:
            try:  # try to find word in top_words for this group, otherwise skip
                sims[p] += top_words[p][w]
            except:
                pass

    return sims


def get_recs(rec_engine, words, group_dfs, top_words, prod_user='user', size=3):
    '''
    takes in list of words and groups, returns recommended products (strains)

    args:
    rec_engine: recommendation engine from graphlab

    if prod_user is 'user', group_dfs should be the user group dfs.
    finds users most similar to words chosen and returns
    recommendations for them from the rec engine

    if prod_user is 'products', group_dfs should be the product group dfs
    finds products most similar to those words (with some randomness)

    words -- list of words chosen by user
    top_words -- dict of words: vector value from get_top_words
    '''
    if prod_user == 'products':
        sims = get_prod_similarity(words, top_words)
        top_idx = np.argsort(list(sims.values()))[::-1]
        # for now return the top 20 most reviewed strains in the category
        prods = group_dfs[top_idx[0]]['product'].value_counts()
        prods20 = prods[:20].index
        return prods, np.random.choice(prods20, size=size, replace=False)

def get_better_recs(link_dict, rec_engine, words, group_dfs, top_words, prod_user='product', size=3):
    '''
    makes improved recommendations
    first, chooses 3 top product groups most similar to chosen words
    then chooses top products from each group that match words best

    takes in list of words and groups, returns recommended products (strains)

    args:
    rec_engine: recommendation engine from graphlab

    if prod_user is 'user', group_dfs should be the user group dfs.
    finds users most similar to words chosen and returns
    recommendations for them from the rec engine

    if prod_user is 'products', group_dfs should be the product group dfs
    finds products most similar to those words (with some randomness)

    words -- list of words chosen by user
    top_words -- dict of words: vector value from get_top_words
    '''
    if prod_user == 'products':
        sims = get_prod_similarity(words, top_words)
        top_idxs = np.argsort(list(sims.values()))[::-1] # highest to lowest relevance
        # for now return the top 20 most reviewed strains in the category
        prods = group_dfs[top_idxs[0]]['product'].value_counts().index
        prods20 = prods[:size * 5]
        links = [link_dict[p] for p in prods]
        links20 = np.array([link_dict[p] for p in prods20])
        idx20 = np.random.choice(list(range(len(prods20))), size=size, replace=False)
        print(idx20)
        return prods, prods[idx20], links, links20[idx20]


def pickle_group_dfs(prod_group_dfs, user_group_dfs, prod_group_dfs_filename='prod_group_dfs.pk', user_group_dfs_filename='user_group_dfs.pk'):
    pk.dump(prod_group_dfs, open(prod_group_dfs_filename, 'w'), 2)
    pk.dump(user_group_dfs, open(user_group_dfs_filename, 'w'), 2)


def load_group_dfs(prod_group_dfs_filename='prod_group_dfs.pk', user_group_dfs_filename='user_group_dfs.pk'):
    prod_group_dfs = pk.load(open(prod_group_dfs_filename))
    user_group_dfs = pk.load(open(user_group_dfs_filename))
    return prod_group_dfs, user_group_dfs


def pickle_top_words(prod_top_words,
                     prod_word_counter,
                     prod_top_words_filename='prod_top_words.pk',
                     prod_word_counter_filename='prod_word_counter.pk'):
    pk.dump(prod_top_words, open(prod_top_words_filename, 'w'), 2)
    pk.dump(prod_word_counter, open(prod_word_counter_filename, 'w'), 2)


def load_top_words(prod_top_words_filename='prod_top_words.pk',
                   prod_word_counter_filename='prod_word_counter.pk'):
    prod_top_words = pk.load(open(prod_top_words_filename))
    prod_word_counter = pk.load(open(prod_word_counter_filename))
    return prod_top_words, prod_word_counter


def train_and_save_everything(filename='leafly/10groupsrec_engine.model'):
    '''
    trains model and pickles and saves everything for later use
    use this if deploying on a server etc
    '''
    df = load_everything(drop=False)
    df2 = dp.get_users_more_than_2_reviews(df)
    df.drop(['date', 'time', 'review'], axis=1, inplace=True)
    df2clean = dp.get_users_more_than_2_reviews(df)
    if os.path.exists(filename):
        rec_engine = load_engine()
    else:
        rec_engine = train_engine(df2clean, max_iterations=400)
        save_engine(rec_engine, filename=filename)

    prod_group_dfs, user_group_dfs = get_latent_feature_groups(rec_engine, df2)
    pickle_group_dfs(prod_group_dfs, user_group_dfs)
    prod_top_words, prod_word_counter = get_top_words(prod_group_dfs)
    pickle_top_words(prod_top_words, prod_word_counter)

    return rec_engine

def make_rec(rec_engine, user, users_in_rec, k=10):
    '''
    makes recommendations for user from rec_engine
    if user not in engine (i.e. less than 2 reviews or new)
    returns None
    '''
    if user in users_in_rec:
        recs = rec_engine.recommend([user], k=k)
        return list(recs['product'])
    else:
        return None

if __name__ == "__main__":
    strains = sl.load_current_strains(True)
    # make dict of names to links for sending links to rec page
    names = [s.split('/')[-1] for s in strains]
    link_dict = {}
    for i, n in enumerate(names):
        link_dict[n] = strains[i]

    rec_engine = load_engine()
    prod_group_dfs, user_group_dfs = load_group_dfs()
    users_in_rec = []
    for u in user_group_dfs:
        users_in_rec.extend(user_group_dfs[u]['user'].values)
    users_in_rec = set(users_in_rec)
    pk.dump(users_in_rec, open('leafly/users_in_rec.pk', 'w'), 2)
    test_product_words = ['intense', 'fruity', 'fire']
    prod_top_words, prod_word_counter = load_top_words()
    prod_top_bigrams, prod_bigram_counter = get_top_ngrams(prod_group_dfs)#load_top_words()
    # recs, top = get_recs(rec_engine, test_product_words,
    #                      prod_group_dfs, prod_top_words, prod_user='products', size=3)
    recs, top, links, toplinks = get_better_recs(link_dict, rec_engine, test_product_words,
                         prod_group_dfs, prod_top_words, prod_user='products', size=50)

    # for checking out the top few words in each group
    df_prod_top_words = {}
    for p in prod_top_words:
        df_prod_top_words[p] = pd.DataFrame({'word':list(prod_top_words[p].keys()), 'vector':list(prod_top_words[p].values())})
        df_prod_top_words[p] = df_prod_top_words[p].sort_values(by='vector', ascending=False)

    for p in df_prod_top_words:
        print(df_prod_top_words[p]['word'].head(20))

    # user_top_words, user_word_counter = get_top_words(user_group_dfs)
    #
    #
    # test_user_words = ['pleasant', 'lemon', 'morning']
    # test_product_words = ['intense', 'fruity', 'fire']
    #
    # sims = get_prod_similarity(test_product_words, prod_top_words)
    # recs = get_recs(rec_engine, test_product_words, prod_group_dfs, prod_top_words, prod_user='products')

    #write_top_words([u for i in user_word_counter], 'user_top_words')
    #top_bigrams, bigram_counter = get_top_ngrams(prod_group_dfs)
