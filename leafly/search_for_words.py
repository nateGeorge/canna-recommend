import leafly.nlp_funcs as nl
import leafly.data_preprocess as dp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#import analytical360.scrape_360 as sc3
import string
import re
from textblob import TextBlob # need this for sentiment analysis

def load_data(full=False):
    # the idea is to find the strains with the most occurances of the word pain
    if full:
        df, prod_df = dp.load_all_full_reviews()
        products = df.groupby('product')
    else:
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
        if full:
            review_list.append(' '.join([r for r in p[1]['full_review']]))
        else:
            review_list.append(' '.join([r for r in p[1]['review']]))

    product_list = np.array(product_list)
    review_counts = np.array(review_counts)
    prod_review_df = pd.DataFrame({'product':product_list, 'review':review_list, 'review_counts':review_counts})

    return df, prod_review_df

def get_top_strains(df, word='pain', plot=False, tfvect=None, review_vects=None, vect_words=None):
    product_list = df['product'].values
    review_counts = df['review_counts'].values
    if tfvect is None and vect_words is None and review_vects is None:
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

    top_strains = zip(product_list[max_pain_sort], review_counts[max_pain_sort])

    return vect_words, review_vects, max_pain_sort, top_strains


if __name__ == "__main__":
    df, prod_review_df = load_data(full=True)
    # review_vects_full = pk.load(open('leafly/review_vects_full.pk'))
    # vect_words = pk.load(open('leafly/vect_words1.pk'))
    tfvect, vect_words, review_vects = nl.lemmatize_tfidf(prod_review_df, max_df=1.0)
    v, r, m, top_strains = get_top_strains(prod_review_df,
                                word='ptsd',
                                review_vects=review_vects,
                                vect_words=vect_words,
                                tfvect=tfvect)

    best_ptsd = []
    please_end = False
    for s in top_strains:
        print s[0]
        if please_end:
            break
        sent_df = nl.get_sents_with_words(df[df['product'] == s[0]], 'ptsd')
        if sent_df['sent_count'].sum() > 5:
            print 'adding...'
            print '!!!!!!!!!!!!!!!!!!!!!!!!!!11'
            sents = ''
            for i, c in sent_df.iterrows():
                sents += ' '.join(c['word_sentence'])

            temp = TextBlob(sents)
            # if temp.sentiment[0] > -1: # range from -1 to 1 but cadillac-purple
            # had 2 negatives and one positive and score 0.475
            best_ptsd.append((s[0], s[1], temp.sentiment[0]))
            if len(best_ptsd) > 5:
                please_end = True



    sent_df = nl.get_sents_with_words(df[df['product'] == 'cadillac-purple'], 'ptsd')
    sents = ''
    for i, c in sent_df.iterrows():
        sents += ' '.join(c['word_sentence'])

    do_lots_of_stuff = False
    if do_lots_of_stuff:
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
