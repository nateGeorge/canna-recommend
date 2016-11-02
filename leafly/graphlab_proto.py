import graphlab as gl
import explore_leafly_data as eld
import data_preprocess as dp



if __name__ == "__main__":

    df = eld.load_data()
    # drop everything but user, product, rating
    df.drop(['date', 'time', 'review'], axis=1, inplace=True)

    # basic rec engine first try
    train, test = dp.make_tt_split(df)

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

    users, products = df.get_users_and_products(df)

    print 'raw mse score:', dp.score_model_mse(test_og.rating, test.rating)

    # optimize num_factors with gridsearch
    from graphlab.toolkits.cross_validation import KFold
    from graphlab.toolkits.model_parameter_search import grid_search

    data = gl.SFrame(df)
    kfolds = KFold(data, 3)
    params = dict([('user_id', 'user'),
                    ('item_id', 'product'),
                    ('target', 'rating'),
                    ('solver', 'auto'),
                    ('num_factors', [2, 3, 4, 5, 6, 10, 20, 32])])
    grid = grid_search.create(kfolds, gl.factorization_recommender.create, params)
    grid.get_results()

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

    # fit a model to the full review set to get latent feature groups

    rec_engine = gl.factorization_recommender.create(observation_data=ratings,
                                                     user_id="user",
                                                     item_id="product",
                                                     target='rating',
                                                     solver='auto',
                                                     num_factors=20
                                                     )

    # assign groups to users and products based on highest coefficient in the matrices
    d = rec_engine.get("coefficients")
    U1 = d['user']
    U2 = d['product']
    U1 = U1['factors'].to_numpy()
    U2 = U2['factors'].to_numpy()

    user_groups = U1.argmax(axis=1)
    prod_groups = U2.argmax(axis=1)

    prod_group_0_df = df[prod_groups == 0]
