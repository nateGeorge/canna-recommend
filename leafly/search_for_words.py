import leafly.nlp_funcs as nl
import leafly.data_preprocess as dp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import analytical360.scrape_360 as sc3
import string
import re

def load_data():
    # the idea is to find the strains with the most occurances of the word pain
    df = dp.load_data()
    products = df.groupby('product')

    # first get a dataframe of products and all their reviews concatenated, so
    # we can do tfidf on each products total reviews
    product_list = []
    review_list = []
    review_counts = []
    for p in products:
        review_counts.append(p[1].shape[0])
        product_list.append(p[0])
        review_list.append(' '.join([r for r in p[1]['review']]))

    product_list = np.array(product_list)
    review_counts = np.array(review_counts)
    prod_review_df = pd.DataFrame({'product':product_list, 'review':review_list, 'review_counts':review_counts})

    return df, prod_review_df

def get_top_strains(df, word='pain', plot=False):
    product_list = df['product'].values
    review_counts = df['review_counts'].values
    tfvect, vect_words, review_vects = nl.lemmatize_tfidf(df, max_df=1.0)
    try:
        pain_idx = np.where(vect_words == word)[0][0]
    except:
        print word, 'not in vectorizer.  Try increasing max/min_df bounds?'
        return None, None, None

    max_pain = np.argmax(review_vects[:, pain_idx])
    max_pain_sort = np.argsort(review_vects[:, pain_idx])[::-1]

    print 'top 10 strains talked about for', word, ':', zip(product_list[max_pain_sort][:10], review_counts[max_pain_sort][:10])

    if plot:
        plt.hist(review_vects[:, pain_idx], bins=50)
        plt.show()

    return vect_words, review_vects, max_pain_sort


if __name__ == "__main__":
    df, prod_review_df = load_data()

    clean_leafly_names = []
    for n in prod_review_df['product']:
        clean_leafly_names.append(re.sub('[ + ' + string.punctuation + '\s]+', '', n).lower())

    prod_review_df['clean_name'] = clean_leafly_names

    leafly_name_set = set(clean_leafly_names)

    cannabinoids, terpenes, no_imgs, im_sources, names = sc3.load_raw_scrape()

    #standardize names for comparing whats in analytical360 and whats from leafly
    clean_360_names = []
    for n in names:
        clean_360_names.append(re.sub('[ + ' + string.punctuation + '\s]+', '', n).lower())

    a360_name_set = set(clean_360_names)

    exact_matches = leafly_name_set.intersection(a360_name_set)

    match_df = prod_review_df[prod_review_df['clean_name'].isin(exact_matches)]

    key_terms = ['pain', 'anxiety', 'sleep', 'depression']
    vect_words, review_vects, max_pain_sort = [], [], []
    for k in key_terms:
        v, r, m = get_top_strains(match_df, word=k)
        vect_words.append(v)
        review_vects.append(r)
        max_pain_sort.append(m)


    # was going to filter products by which have been tested,
    # but just do the get_top_strains on a pre-filtered DF
    # topNames = prod_review_df['clean_name'].iloc[max_pain_sort]
    # topNamesChem = topNames.copy()
    # keepNames = []
    # for n in topNames.iterrows():
    #     name = n['clean_name']
    #     if name in exact_matches:
    #         keepNames.append()
