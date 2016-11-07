from sklearn.model_selection import train_test_split as tts
from sklearn.metrics import mean_squared_error as mse
from pymongo import MongoClient
import pandas as pd
import numpy as np
import re

DB_NAME = 'leafly_backup_2016-11-01'  # 'leafly'

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


def load_data(fix_names=True, clean_reviews=True):
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
    df = df[df['user'] != 'Anonymous']
    df = df.drop_duplicates(subset=[u'product', u'rating', u'review', u'user'])
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
