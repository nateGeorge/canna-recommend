from sklearn.model_selection import train_test_split as tts
from sklearn.metrics import mean_squared_error as mse
from pymongo import MongoClient
import pandas as pd
import numpy as np
import re

DB_NAME = 'leafly_backup_2016-11-01'  # 'leafly'

def load_all_full_reviews():
    '''
    loads df of partial reviews, and df of full reviews and merges
    one-hot encodes flavors and effects
    also returns a product df where the flavors and effects have been normalized
    to a % for each product
    '''
    client = MongoClient()
    db = client['leafly_full_reviews']
    coll = db['full_reviews']


    effects = []
    effects_list = []
    flavors = []
    flavors_list = []
    forms = []
    methods = []
    full_reviews = []
    links = []
    isok = []
    locations = []
    locations_list = []

    for d in coll.find():
        effects.append('-'.join(d['effects']))
        effects_list.extend(d['effects'])
        flavors.append('-'.join(d['flavors']))
        flavors_list.extend(d['flavors'])
        forms.append(d['form'])
        methods.append(d['method'])
        full_reviews.append(d['full_review'])
        isok.append(d['isok'])
        locations.append(d['locations'])
        locations_list.append(d['locations'])
        links.append(d['link'])

    full_rev_df = pd.DataFrame({'effects':effects,
                                'flavors':flavors,
                                'form':forms,
                                'method':methods,
                                'full_review':full_reviews,
                                'isok':isok,
                                'locations':locations,
                                'link':links})

    orig_df = load_data(no_anon=False, get_links=True)

    full_df = full_rev_df.merge(orig_df, on='link')

    # one-hot encode effects
    unique_effects = set(np.unique(effects_list))
    effect_dict = {}
    for i, r in full_df.iterrows():
        temp_ef = set()
        if r['effects'] != '':
            temp_ef = set([s.strip() for s in r['effects'].split('-')])
            if '' in temp_ef:
                print(r)
                break
            for e in temp_ef:
                effect_dict.setdefault(e, []).append(1)
        for e in unique_effects.difference(temp_ef):
            effect_dict.setdefault(e, []).append(0)

    effect_dict['link'] = full_df['link'].values
    # check to make sure lengths are the same
    for k in list(effect_dict.keys()):
        print(k, len(effect_dict[k]))

    # one-hot encode flavors
    unique_flavors = set(np.unique(flavors_list))
    flavor_dict = {}
    for i, r in full_df.iterrows():
        temp_fl = set()
        if r['flavors'] != '':
            temp_fl = set([s.strip() for s in r['flavors'].split('-')])
            if '' in temp_fl:
                print(r)
                break
            for e in temp_fl:
                flavor_dict.setdefault(e, []).append(1)
        for e in unique_flavors.difference(temp_fl):
            flavor_dict.setdefault(e, []).append(0)

    flavor_dict['link'] = full_df['link'].values

    flavor_df = pd.DataFrame(flavor_dict, dtype='float64')
    effect_df = pd.DataFrame(effect_dict, dtype='float64')
    ohe_df = full_df.merge(effect_df, on='link')
    ohe_df = ohe_df.merge(flavor_df, on='link')
    prod_ohe = ohe_df.groupby('product').sum()
    # normalize the count of each characteristic to make it a % of total for each product
    for i, r in prod_ohe.iterrows():
        sumcount = np.sum([r[c] for c in unique_effects])
        if sumcount == 0:
            continue
        for c in unique_effects:
            prod_ohe = prod_ohe.set_value(i, c, r[c] / float(sumcount))

        sumcount = np.sum([r[c] for c in unique_effects])
        print(sumcount)

    for i, r in prod_ohe.iterrows():
        sumcount = np.sum([r[c] for c in unique_flavors])
        if sumcount == 0:
            continue
        for c in unique_flavors:
            prod_ohe = prod_ohe.set_value(i, c, r[c] / float(sumcount))

        sumcount = np.sum([r[c] for c in unique_flavors])
        print(sumcount)

    return ohe_df, prod_ohe

def get_users_more_than_2_reviews(df):
    '''
    filters dataframe to only included users with more than 2 reviews
    '''
    new_df = df.copy()
    users = df.groupby('user').count()
    gt2 = set(users[users['product'] > 2].index)
    new_df = new_df[new_df['user'].isin(gt2)]
    return new_df

def clean_reviews_func(df):
    '''
    removes the last word in long reviews, since it is mashed up with '...'

    takes in raw dataframe of review data

    returns dataframe with cleaned reviews
    '''
    df['review'] = df['review'].apply(
        lambda x: re.sub('[A-Za-z0-9]*\.\.\.', '', x))
    return df


def load_data(fix_names=True, clean_reviews=True, no_anon=True, get_links=False):
    '''
    loads all review data into pandas DataFrame
    if fix_name==True, will fix the encoded names to their readable parallels
    '''
    client = MongoClient()
    db = client[DB_NAME]
    total = 0

    product_renames = {'0bf3f759-186e-4dad-89d0-e0fc7598ac53': 'berry-white',
                       '29aca226-23ba-4726-a4ab-f3bf68f2a3c4': 'dynamite',
                       'c42aa00a-595a-4e58-a7af-0f8ab998073a': 'kaboom'}
    coll_skips = set(
        ['system.indexes', 'review_counts', 'scraped_review_pages'])
    products = []
    ratings = []
    reviews = []
    dates = []
    users = []
    links = []
    for c in db.collection_names():
        if c in coll_skips:
            continue

        everything = db[c].find({"scrape_times": {"$exists": False},
                                 "review_count": {"$exists": False},
                                 "genetics": {"$exists": False}
                                 })
        for e in everything:
            products.append(c)
            ratings.append(float(e['stars']))
            reviews.append(e['text'])
            dates.append(e['date'])
            users.append(e['user'])
            if get_links:
                links.append(e['link'])

    if get_links:
        df = pd.DataFrame({'rating': ratings, 'review': reviews,
                        'date': dates, 'user': users, 'product': products, 'link': links})
    else:
        df = pd.DataFrame({'rating': ratings, 'review': reviews,
                        'date': dates, 'user': users, 'product': products})
    if clean_reviews:
        df = clean_reviews_func(df)
    if fix_names:
        for p in product_renames:
            df['product'][df['product'] == p] = product_renames[p]

    dates = pd.to_datetime(df['date'])
    df['date'] = dates.apply(lambda x: x.date())
    df['time'] = dates.apply(lambda x: x.time())
    if no_anon:
        df = df[df['user'] != 'Anonymous']

    df = df.drop_duplicates(subset=['product', 'rating', 'review', 'user'])
    return df


def make_tt_split(df):
    '''
    takes a reviews dataframe as input args

    returns train and test set dataframes with user, review, and product
    '''
    traindf, testdf = tts(df, random_state=42)

    return traindf, testdf


def score_model_mse(y_true, y_pred):
    return mse(y_true, y_pred)


def get_users_and_products(df):
    '''
    takes in raw dataframe of reviews
    filters out review by 'Anonymous'
    return dataframes of reviews grouped by users and products
    '''
    df_no_anon = df[df['user'] != 'Anonymous']
    users = df_no_anon.groupby('user').count()
    products = df_no_anon.groupby('product').count()

    return users, products
