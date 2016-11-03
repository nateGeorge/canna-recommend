import spacy
import numpy as np
import re
import string
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
np.random.seed(42)

def get_stopwords():
    # words I noticed came up in the first tfidf run, which should be excluded
    EXTRA_STOP_WORDS = ['strain', 'high', 'great', 'good', 'nice', 'like', 'taste',
                        'really', 'love', 'smell', 'smoke', 'favorite', 'best', ]

    ESW2 = [u'amazing',
             u'blue',
             u'dream',
             u'happy',
             u'head',
             u'pain',
             u'relaxing',
             u'sleep',
             u'sour',
             u'strong',
             u'sweet',
             u'time']


    stops = set(list(stopwords.words('english'))) | set(EXTRA_STOP_WORDS) | set(ESW2)

    return stops

def clean_article(article):
    nlp = spacy.load('en')

    # Create custom stoplist
    STOPLIST = set(stopwords.words('english') + ["n't", "'s", "'m", "ca", "'", "'re"] + list(ENGLISH_STOP_WORDS))
    PUNCT_DICT = {ord(punc): None for punc in punctuation if punc not in ['_', '*']}

    doc = nlp(article)

    # Let's merge all of the proper entities
    for ent in doc.ents:
        if ent.root.tag_ != 'DT':
            ent.merge(ent.root.tag_, ent.text, ent.label_)
        else:
            # Keep entities like 'the New York Times' from getting dropped
            ent.merge(ent[-1].tag_, ent.text, ent.label_)

    # Part's of speech to keep in the result
    pos_lst = ['ADJ', 'ADV', 'NOUN', 'PROPN', 'VERB'] # NUM?

    tokens = [token.lemma_.lower().replace(' ', '_') for token in doc if token.pos_ in pos_lst]

    return ' '.join(token for token in tokens if token not in STOPLIST).replace("'s", '').translate(PUNCT_DICT)

def get_top_words(df, num_words=10):
    '''
    gets top words from tfidf vectorization of reviews in dataframe df

    input:
    df -- dataframe with 'review' column
    num_words -- number of top words to return (ranked by tfidf)

    output:
    list of top words ranked in order
    '''
    stops = get_stopwords()
    reviews = df['review'].values
    reviews = [s.encode('ascii', errors='ignore') for s in reviews]

    tfvect = TfidfVectorizer(stop_words=stops, max_df=0.75, min_df=5)
    review_vects = tfvect.fit_transform(reviews)
    vect_words = np.array(tfvect.get_feature_names())
    review_vects = review_vects.toarray()
    avg_vects = review_vects.mean(axis=0)
    sort_idxs = np.array(np.argsort(avg_vects))[::-1]
    return vect_words[sort_idxs][:10]

def get_top_bigrams(df, num_words=10):
    '''
    gets top words from tfidf vectorization of reviews in dataframe df

    input:
    df -- dataframe with 'review' column
    num_words -- number of top words to return (ranked by tfidf)

    output:
    list of top words ranked in order
    '''
    stops = get_stopwords()
    reviews = df['review'].values
    reviews = [s.encode('ascii', errors='ignore') for s in reviews]

    tfvect = TfidfVectorizer(stop_words=stops, max_df=0.5, min_df=5, ngram_range=(2, 2))
    review_vects = tfvect.fit_transform(reviews)
    vect_words = np.array(tfvect.get_feature_names())
    review_vects = review_vects.toarray()
    avg_vects = review_vects.mean(axis=0)
    sort_idxs = np.array(np.argsort(avg_vects))[::-1]
    return vect_words[sort_idxs][:10]

def words_choices():
    '''
    returns list of words that can be used as choices in initialization function
    for recommendations for someone without any reviews
    '''
    # couch lock was in every document with bigrams, so was 'long lasting' with max_df=0.75
    'wake bake', 'body buzz', 'couch lock', 'clear headed', 'fruity pebbles', 'juicy fruit', 'long lasting'