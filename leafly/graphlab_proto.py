import graphlab as gl
import data_preprocess as dp
from graphlab.toolkits.cross_validation import KFold
from graphlab.toolkits.model_parameter_search import grid_search
import nlp_funcs as nl
from collections import Counter
import pandas as pd

def basic_fr(train, test):
    '''
    trains a default factorization_recommender on a train set and scores on
    test set

    args:
    train and test dataframes
    returns:
    graphlab recommendation engine
    '''
    test_og = test.copy()

    ratings = gl.SFrame(train)
    testsl = gl.SFrame(test)
    rec_engine = gl.factorization_recommender.create(observation_data=ratings,
                                                     user_id="user",
                                                     item_id="product",
                                                     target='rating',
                                                     solver='auto',
                                                     num_factors=32 # 32 by default
                                                     )

    test.rating = rec_engine.predict(testsl)
    test.to_csv('test_predictions.csv', index=False, encoding='utf-8')

    print 'raw mse score:', dp.score_model_mse(test_og.rating, test.rating)

    return rec_engine

def gridsearch_big_step(df):
    '''
    gridsearches num_factors for the factorization_recommender in larger steps
    args: dataframe, df

    returns: gridsearch object
    '''
    data = gl.SFrame(df)
    kfolds = KFold(data, 3)
    params = dict([('user_id', 'user'),
                    ('item_id', 'product'),
                    ('target', 'rating'),
                    ('solver', 'auto'),
                    ('num_factors', [2, 3, 4, 5, 6, 10, 20, 32])])
    grid = grid_search.create(kfolds, gl.factorization_recommender.create, params)
    grid.get_results()

    return grid

    # results:

    '''
        +---------+-------------+--------+--------+---------+--------------+
    | item_id | num_factors | solver | target | user_id |   model_id   |
    +---------+-------------+--------+--------+---------+--------------+
    | product |      6      |  auto  | rating |   user  | [13, 12, 14] |
    | product |      2      |  auto  | rating |   user  |  [1, 0, 2]   |
    | product |      3      |  auto  | rating |   user  |  [3, 5, 4]   |
    | product |      4      |  auto  | rating |   user  |  [8, 7, 6]   |
    | product |      20     |  auto  | rating |   user  | [19, 18, 20] |
    | product |      32     |  auto  | rating |   user  | [21, 23, 22] |
    | product |      5      |  auto  | rating |   user  | [9, 11, 10]  |
    | product |      10     |  auto  | rating |   user  | [15, 17, 16] |
    +---------+-------------+--------+--------+---------+--------------+
    +----------------------+--------------------+------------------------+
    | mean_validation_rmse | mean_training_rmse | mean_training_recall@5 |
    +----------------------+--------------------+------------------------+
    |    1.00678522065     |   0.323030678029   |   0.000154761649416    |
    |     1.0208240936     |   0.453632730191   |   0.000122923478199    |
    |    1.00833928422     |   0.399805022552   |   0.000122507107597    |
    |    1.00770345896     |   0.362172915738   |   0.000107193018127    |
    |    0.983536655638    |   0.242915200506   |    0.00432907413023    |
    |    0.983353577078    |   0.24082851848    |    0.00435477863392    |
    |    1.00653732816     |   0.344224040089   |   0.000194937374462    |
    |    0.986200185618    |   0.272243232275   |    0.00193547952321    |
    +----------------------+--------------------+------------------------+
    +--------------------------+-----------+-----------------------------+-----------+
    | mean_validation_recall@5 |  fold_id  | mean_validation_precision@5 | num_folds |
    +--------------------------+-----------+-----------------------------+-----------+
    |    2.22170382466e-06     | [1, 0, 2] |      2.22170382466e-06      |     3     |
    |           0.0            | [1, 0, 2] |             0.0             |     3     |
    |           0.0            | [0, 2, 1] |             0.0             |     3     |
    |           0.0            | [2, 1, 0] |             0.0             |     3     |
    |    2.55287233685e-05     | [1, 0, 2] |      5.10991879673e-05      |     3     |
    |    3.18371310973e-05     | [0, 2, 1] |      3.77689650193e-05      |     3     |
    |           0.0            | [0, 2, 1] |             0.0             |     3     |
    |    1.58848655361e-05     | [0, 2, 1] |      1.55519267726e-05      |     3     |
    +--------------------------+-----------+-----------------------------+-----------+
    +---------------------------+
    | mean_training_precision@5 |
    +---------------------------+
    |     0.000139302381458     |
    |      0.0001082603732      |
    |     0.000133943316761     |
    |     0.000108451292331     |
    |      0.00392953856325     |
    |      0.00397506409151     |
    |      0.0001511569914      |
    |      0.00165102804133     |
    +---------------------------+
    '''

    '''
    looks like 20 features is a decent number.  need to gridsearch more later in the range 10-30
    '''

def gridsearch_10_20(df):
    '''
    gridsearches num_factors for the factorization_recommender in range 20-30
    args: dataframe, df

    returns: gridsearch object
    '''
    data = gl.SFrame(df)
    kfolds = KFold(data, 3)
    params = dict([('user_id', 'user'),
                    ('item_id', 'product'),
                    ('target', 'rating'),
                    ('solver', 'auto'),
                    ('num_factors', range(20, 31))])
    grid = grid_search.create(kfolds, gl.factorization_recommender.create, params)
    grid.get_results()

    return grid


if __name__ == "__main__":

    df = dp.load_data()
    # drop everything but user, product, rating
    df.drop(['date', 'time', 'review'], axis=1, inplace=True)
    # remove user 'Anonymous' -- necessary to match up size of products from
    # data_preprocess get users and products func
    df_no_anon = df[df['user'] != 'Anonymous']

    # basic rec engine first try
    train, test = dp.make_tt_split(df)

    # trains and scores a basic factorization_recommender
    #basic_fr(train, test)

    # gridsearches over larger steps
    #gridsearch_big_step(df)

    # fit a model to the full review set to get latent feature groups

    data = gl.SFrame(df)
    num_factors = 20
    rec_engine = gl.factorization_recommender.create(observation_data=data,
                                                     user_id="user",
                                                     item_id="product",
                                                     target='rating',
                                                     solver='auto',
                                                     num_factors=num_factors
                                                     )

    # assign groups to users and products based on highest coefficient in the matrices
    d = rec_engine.get("coefficients")
    U1 = d['user']
    U2 = d['product']
    U1 = U1['factors'].to_numpy()
    U2 = U2['factors'].to_numpy()

    user_groups = U1.argmax(axis=1)
    prod_groups = U2.argmax(axis=1)

    users, products = dp.get_users_and_products(df)

    full_df = dp.load_data()
    prod_group_dict = {}
    prod_group_dfs = {}
    for i in range(num_factors):
        # this gets the product names in each group
        prod_list = products[prod_groups == i].index
        prod_group_dict[i] = prod_list
        prod_list = set(prod_list)
        # this will get dataframes from the main df with products in each group
        prod_group_dfs[i] = full_df[full_df['product'].isin(prod_list)]

    import nlp_funcs as nl
    top_words = {}
    top_words_set = set()
    word_list = []
    for i in range(num_factors):
        words = nl.get_top_words(prod_group_dfs[i])
        top_words_set = top_words_set | set(words)
        top_words[i] = words
        word_list.extend(words)

    word_counter = Counter(word_list)

    # try lemmatization
    import nlp_funcs as nl
    top_words = {}
    top_words_set = set()
    word_list = []
    for i in range(num_factors):
        words = nl.get_top_words_lemmatize(prod_group_dfs[i], 50)
        top_words_set = top_words_set | set(words)
        top_words[i] = words
        word_list.extend(words)

    word_counter = Counter(word_list)

    # try bigrams
    import nlp_funcs as nl
    top_words = {}
    top_words_set = set()
    word_list = []
    for i in range(num_factors):
        words = nl.get_top_bigrams(prod_group_dfs[i])
        top_words_set = top_words_set | set(words)
        top_words[i] = words
        word_list.extend(words)

    word_counter = Counter(word_list)

    # get strain list so we can exclude it from bigrams
    import scrape_leafly as sl
    strains = sl.load_current_strains(correct_names=True)
    strains_split = [s.split('/') for s in strains]
    strain_info = [(s[1].lower(), s[2].lower(), re.sub('-', ' ', s[2].lower())) for s in strains_split]
    # maps strain to category (hybrid, indica, sativa, edible) in each group
    strain_cat_dict = {}
    for s in strain_info:
        strain_cat_dict[s[1]] = s[0]

    # get % of each type (hybrid, indica, sativa, edible) in each group
    prod_group_pcts = {}
    for p in prod_group_dfs:
        temp_df = prod_group_dfs[p]
        temp_df['category'] = temp_df['product'].map(lambda x: strain_cat_dict[x])
        prod_group_dfs[p] = temp_df
        cat_val_counts_p = prod_group_dfs[p]['category'].value_counts()
        prod_group_pcts[p] = [round(float(c)/prod_group_dfs[p].shape[0]*100, 2) for c in cat_val_counts_p]
        prod_group_pcts[p] = pd.Series(data=prod_group_pcts[p], index=cat_val_counts_p.index)


    # get % of each type overall
    full_df['category'] = full_df['product'].map(lambda x: strain_cat_dict[x])
    cat_val_counts = full_df['category'].value_counts()
    print cat_val_counts
    cat_val_pct = [round(float(c)/full_df.shape[0]*100, 2) for c in cat_val_counts]
    cat_val_pct = pd.Series(data=cat_val_pct, index=cat_val_counts.index)

    print top_words_set # without any stopwords: [u'good', u'pain', u'taste', u'high', u'strain', u'love', u'best', u'really', u'great', u'like', u'favorite', u'smoke', u'time', u'smell', u'nice']
