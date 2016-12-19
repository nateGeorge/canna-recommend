import leafly.nlp_funcs as nl
import leafly.data_preprocess as dp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#import analytical360.scrape_360 as sc3
import string
import re
from textblob import TextBlob # need this for sentiment analysis
import cPickle as pk
import os
import easygui as eg
from time import time

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
    '''
    takes a dataframe with products, reviews, and review counts,
    and sorts by word in tfidf of reviews for each strain

    returns tuple of:
        list of vectorized words
        list of tfidf vectors
        sorted review_vector by the word
        top strains: a tuple of product (strain) and total review counts
    '''
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


def get_top_strains_word_sentiment(prod_review_df, word='ptsd', min_sents=1,
                                    early_stop=False, yes_pickle=True):
    '''
    gets all strains that contain the word at least min_sents number of times
    returns
    args:
    prod_review_df -- dataframe with product reviews; must have 'prodect' and 'review' columns
    word -- the word to look for in the reviews
    min_sents -- the minimum number of times the word appears in reviews
    early_stop -- if True, will stop after 5 strains with the word have been found
    pickle -- if True, will save results in a pickled file for faster loading next time;
            and will load from pickle file if available
    returns:
    dataframe of product, review, sentiment of concatenated reviews
    dataframe of product, review sentence, sentiment of sentence

    '''
    if yes_pickle:
        if os.path.exists(word + '_senti_df.pk'):
            senti_df = pk.load(open(word + '_senti_df.pk'))
            sent_df = pk.load(open(word + '_sent_df.pk'))
            return senti_df, sent_df
        else:
            print 'file doesn\'t exist, creating from scratch...'

    start_time = time()
    if not os.path.exists('leafly/tfvect.pk'):
        tfvect, vect_words, review_vects = nl.lemmatize_tfidf(prod_review_df, max_df=1.0)
    else:
        tfvect = pk.load(open('leafly/tfvect.pk'))
        vect_words = pk.load(open('leafly/vect_words.pk'))
        review_vects = pk.load(open('leafly/review_vects.pk'))

    v, r, m, top_strains = get_top_strains(prod_review_df,
                                word='ptsd',
                                review_vects=review_vects,
                                vect_words=vect_words,
                                tfvect=tfvect)

    best_ptsd = []
    please_end = False
    sentiment_dict = {}
    sentence_df = None
    early_counter = 0
    for s in top_strains:
        if please_end:
            break
        sent_df = nl.get_sents_with_words(df[df['product'] == s[0]], 'ptsd')
        if sentence_df is None:
            sentence_df = sent_df
        else:
            sentence_df = sentence_df.append(sent_df)

        if sent_df['sent_count'].sum() > min_sents:
            early_counter += 1
            print '[HAS WORD]: adding', s[0]
            sents = ''
            for i, c in sent_df.iterrows():
                # separate sentences by something unique so we can split them again later
                sents += '||--||' + ' '.join(c['word_sentence'])

            temp = TextBlob(sents)
            # if temp.sentiment[0] > -1: # range from -1 to 1 but cadillac-purple
            # had 2 negatives and one positive and score 0.475
            sentiment_dict.setdefault('strain', []).append(s[0])
            sentiment_dict.setdefault('num_reviews', []).append(s[1])
            sentiment_dict.setdefault('sentiment_score', []).append(temp.sentiment[0])
            sentiment_dict.setdefault('review_text', []).append(sents)
            best_ptsd.append((s[0], s[1], temp.sentiment[0]))
            if early_stop and early_counter == 5:
                break
        else:
            print s[0]

    print 'top 10 strains:', sorted(best_ptsd, key=lambda x: x[2], reverse=True)[:10]
    sentence_df = sentence_df[sentence_df['sent_count'] >= 1]
    sentence_df['first_sentence'] = sentence_df['word_sentence'].apply(lambda x: x[0])
    sentence_df['sentiment_score'] = sentence_df['first_sentence'].apply(lambda x: get_sentiment(x))

    print 'took', (time() - start_time) / 1000., 'seconds'
    if yes_pickle:
        pk.dump(senti_df, open(word + '_senti_df.pk', 'w'))
        pk.dump(sent_df, open(word + '_sent_df.pk', 'w'))
    
    return pd.DataFrame(sentiment_dict), sentence_df

def get_sentiment(sentence):
    '''
    gets sentiment from sentence using textblob
    '''
    blob = TextBlob(sentence)
    return blob.sentiment[0]

def score_sentiments(df):
    '''
    takes a dataframe with product, review text in it
    displays one review text at a time, user rates sentiment -1, 0, or 1
    '''
    print '''press 1 to rate sentence as positive sentiment,
            0 as negative,
            and . as neutral.
            Press enter to finish that entry.
            '''
    ratings = []
    for i, c in df.iterrows():
        print ''
        print c['first_sentence']
        rating = raw_input()
        ratings.append(rating)

    return ratings





if __name__ == "__main__":
    df, prod_review_df = load_data(full=True)
    # review_vects_full = pk.load(open('leafly/review_vects_full.pk'))
    # vect_words = pk.load(open('leafly/vect_words1.pk'))

    # gets top words with default args, 'ptsd' and pickles it
    senti_df, sent_df = get_top_strains_word_sentiment(prod_review_df)#, early_stop=True)

    # makes full tfidf vectors
    makeFull = False
    if makeFull:
        tfvect, vect_words, review_vects = nl.lemmatize_tfidf(prod_review_df, max_df=1.0)
        pk.dump(tfvect, open('leafly/tfvect.pk', 'w'), 2)
        pk.dump(vect_words, open('leafly/vect_words.pk', 'w'), 2)
        pk.dump(review_vects, open('leafly/review_vects.pk', 'w'), 2)


    do_lots_of_stuff = False
    if do_lots_of_stuff:
        sent_df = nl.get_sents_with_words(df[df['product'] == 'cadillac-purple'], 'ptsd')
        sents = ''
        for i, c in sent_df.iterrows():
            sents += ' '.join(c['word_sentence'])

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
