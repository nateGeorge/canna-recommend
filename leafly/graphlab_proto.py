import graphlab as gl
import data_preprocess as dp
from graphlab.toolkits.cross_validation import KFold
from graphlab.toolkits.model_parameter_search import grid_search
import nlp_funcs as nl
from collections import Counter
import pandas as pd
import scrape_leafly as sl

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

def gridsearch_alot(df):
    '''
    gridsearches num_factors for the factorization_recommender in range 2-32
    args: dataframe, df

    returns: gridsearch object
    '''
    data = gl.SFrame(df)
    kfolds = KFold(data, 3)
    num_factors_space = list(range(20, 31))
    num_factors_space.extend([2, 4, 6, 8, 10, 12, 16, 32])
    num_factors_space = sorted(num_factors_space)
    params = dict([('user_id', 'user'),
                    ('item_id', 'product'),
                    ('target', 'rating'),
                    ('solver', 'auto'),
                    ('num_factors', num_factors_space)])
    grid = grid_search.create(kfolds, gl.factorization_recommender.create, params)
    grid.get_results()

    return grid


if __name__ == "__main__":

    df = dp.load_data()
    # drop everything but user, product, rating
    df.drop(['date', 'time', 'review'], axis=1, inplace=True)
    grid = gridsearch_alot(df)
    print grid.get_results()
    # remove user 'Anonymous' -- necessary to match up size of products from
    # data_preprocess get users and products func

    # basic rec engine first try
    #train, test = dp.make_tt_split(df)

    # trains and scores a basic factorization_recommender
    #basic_fr(train, test)

    # gridsearches over larger steps
    #gridsearch_big_step(df)

    # fit a model to the full review set to get latent feature groups

    # data = gl.SFrame(df)
    # num_factors = 20
    # rec_engine = gl.factorization_recommender.create(observation_data=data,
    #                                                  user_id="user",
    #                                                  item_id="product",
    #                                                  target='rating',
    #                                                  solver='auto',
    #                                                  num_factors=num_factors
    #                                                  )
    #
    # # assign groups to users and products based on highest coefficient in the matrices
    # d = rec_engine.get("coefficients")
    # U1 = d['user']
    # U2 = d['product']
    # U1 = U1['factors'].to_numpy()
    # U2 = U2['factors'].to_numpy()
    #
    # user_groups = U1.argmax(axis=1)
    # prod_groups = U2.argmax(axis=1)
    #
    # users, products = dp.get_users_and_products(df)
    #
    # full_df = dp.load_data()
    # prod_group_dict = {}
    # prod_group_dfs = {}
    # for i in range(num_factors):
    #     # this gets the product names in each group
    #     prod_list = products[prod_groups == i].index
    #     prod_group_dict[i] = prod_list
    #     prod_list = set(prod_list)
    #     # this will get dataframes from the main df with products in each group
    #     prod_group_dfs[i] = full_df[full_df['product'].isin(prod_list)]
    #
    # top_words = {}
    # top_words_set = set()
    # word_list = []
    # for i in range(num_factors):
    #     words = nl.get_top_words(prod_group_dfs[i])
    #     top_words_set = top_words_set | set(words)
    #     top_words[i] = words
    #     word_list.extend(words)
    #
    # word_counter = Counter(word_list)
    #
    # # try lemmatization
    # top_words = {}
    # top_words_set = set()
    # word_list = []
    # for i in range(num_factors):
    #     words = nl.get_top_words_lemmatize(prod_group_dfs[i], 50)
    #     top_words_set = top_words_set | set(words)
    #     top_words[i] = words
    #     word_list.extend(words)
    #
    # word_counter = Counter(word_list)

    '''
    gave this:

    ({u'also': 19,
         u'always': 1,
         u'anxiety': 20,
         u'atf': 1,
         u'awesome': 19,
         u'back': 2,
         u'beautiful': 1,
         u'bit': 1,
         u'blackberry': 1,
         u'blueberry': 1,
         u'body': 20,
         u'bubba': 1,
         u'bud': 20,
         u'buzz': 19,
         u'cheese': 2,
         u'chemdawg': 1,
         u'couch': 10,
         u'crack': 1,
         u'day': 20,
         u'definitely': 20,
         u'diesel': 1,
         u'earthy': 2,
         u'effect': 20,
         u'energetic': 3,
         u'energy': 1,
         u'euphoric': 13,
         u'ever': 20,
         u'far': 1,
         u'feel': 20,
         u'feeling': 20,
         u'felt': 14,
         u'first': 20,
         u'flavor': 20,
         u'fruity': 1,
         u'gdp': 1,
         u'get': 20,
         u'give': 18,
         u'go': 19,
         u'got': 20,
         u'green': 1,
         u'gsc': 1,
         u'ha': 20,
         u'haze': 2,
         u'headband': 1,
         u'heavy': 14,
         u'help': 7,
         u'hit': 20,
         u'hybrid': 1,
         u'indica': 20,
         u'insomnia': 1,
         u'jack': 1,
         u'kush': 8,
         u'lemon': 4,
         u'little': 19,
         u'long': 20,
         u'made': 19,
         u'make': 20,
         u'mellow': 14,
         u'much': 20,
         u'night': 15,
         u'og': 3,
         u'one': 20,
         u'orange': 1,
         u'perfect': 20,
         u'pineapple': 1,
         u'potent': 8,
         u'pretty': 20,
         u'purple': 2,
         u'recommend': 20,
         u'relaxed': 20,
         u'relief': 5,
         u'right': 2,
         u'sativa': 20,
         u'shit': 6,
         u'smoked': 20,
         u'smoking': 18,
         u'smooth': 20,
         u'still': 8,
         u'stress': 2,
         u'stuff': 20,
         u'super': 20,
         u'tasty': 1,
         u'top': 5,
         u'uplifting': 15,
         u'wa': 20,
         u'weed': 19,
         u'well': 20,
         u'white': 1,
         u'widow': 1,
         u'would': 20})

         words to use for feeling:
         uplifting, mellow, euphoric, euphoria, energy, energetic, relief
         words to use for taste:
         potent, pineapple, orange, lemon, earthy, diesel, blackberry, blueberry, cherry, banana
         words to use for conditions:
         insomnia, stress, headache, depression, anxiety
         words to use for effects:
         body, couch, mellow, focus, focused, cerebral
         times:
         daytime, night

         words to include in stoplist:
         weed, wa, well, white, widow, would, tasty, top, stuff, super, still, smooth, smoked,
         smoking, shit, sativa, right, relaxed, recommend, purple, pretty, og, one, perfect,
         far, feel, feeling, first, flavor, long, made, make, mellow, much, night, little, kush,
         jack, indica, hybrid, hit, help, heavy, headband, haze, ha, gsc, green, got, go, give,
         get, gdp, ever, always, atf, awesome, beautiful, bit, bubba, bud, buzz, chemdawg,
         crack, definitely, effect
    '''

    # try bigrams
    # top_words = {}
    # top_words_set = set()
    # word_list = []
    # for i in range(num_factors):
    #     words = nl.get_top_bigrams(prod_group_dfs[i])
    #     top_words_set = top_words_set | set(words)
    #     top_words[i] = words
    #     word_list.extend(words)
    #
    # word_counter = Counter(word_list)
    #
    # # get strain list so we can exclude it from bigrams
    # strains = sl.load_current_strains(correct_names=True)
    # strains_split = [s.split('/') for s in strains]
    # strain_info = [(s[1].lower(), s[2].lower(), re.sub('-', ' ', s[2].lower())) for s in strains_split]
    # # maps strain to category (hybrid, indica, sativa, edible) in each group
    # strain_cat_dict = {}
    # for s in strain_info:
    #     strain_cat_dict[s[1]] = s[0]
    #
    # # get % of each type (hybrid, indica, sativa, edible) in each group
    # prod_group_pcts = {}
    # for p in prod_group_dfs:
    #     temp_df = prod_group_dfs[p]
    #     temp_df['category'] = temp_df['product'].map(lambda x: strain_cat_dict[x])
    #     prod_group_dfs[p] = temp_df
    #     cat_val_counts_p = prod_group_dfs[p]['category'].value_counts()
    #     prod_group_pcts[p] = [round(float(c)/prod_group_dfs[p].shape[0]*100, 2) for c in cat_val_counts_p]
    #     prod_group_pcts[p] = pd.Series(data=prod_group_pcts[p], index=cat_val_counts_p.index)
    #
    #
    # # get % of each type overall
    # full_df['category'] = full_df['product'].map(lambda x: strain_cat_dict[x])
    # cat_val_counts = full_df['category'].value_counts()
    # print cat_val_counts
    # cat_val_pct = [round(float(c)/full_df.shape[0]*100, 2) for c in cat_val_counts]
    # cat_val_pct = pd.Series(data=cat_val_pct, index=cat_val_counts.index)
    #
    # print top_words_set # without any stopwords: [u'good', u'pain', u'taste', u'high', u'strain', u'love', u'best', u'really', u'great', u'like', u'favorite', u'smoke', u'time', u'smell', u'nice']
