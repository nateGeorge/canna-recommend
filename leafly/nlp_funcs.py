import leafly.data_preprocess as dp
import re
import spacy
import numpy as np
import re
import string
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from spacy.en import English
import pickle as pk

parser = English()

np.random.seed(42)

# actually from the graphlab_production.py file, but can't import due to
# circular importing...
def load_group_dfs(prod_group_dfs_filename='prod_group_dfs.pk', user_group_dfs_filename='user_group_dfs.pk'):
    prod_group_dfs = pk.load(open(prod_group_dfs_filename))
    user_group_dfs = pk.load(open(user_group_dfs_filename))
    return prod_group_dfs, user_group_dfs


def print_fine_pos(token):
    return (token.tag_)


def pos_tags(sentence):
    '''
    args:
    sentence -- unicode string
    '''
    nlp = spacy.load('en')
    #sentence = sentence.encode("utf-8")
    tokens = nlp(sentence)
    tags = []
    for tok in tokens:
        tags.append((tok, print_fine_pos(tok)))
    return tags


def get_stopwords():
    # words I noticed came up in the first tfidf run, which should be excluded
    EXTRA_STOP_WORDS = ['strain', 'high', 'great', 'good', 'nice', 'like', 'taste',
                        'really', 'love', 'smell', 'smoke', 'favorite', 'best']

    ESW2 = ['amazing',
            u'blue',
            u'dream',
            u'happy',
            # u'head',
            # u'pain',
            # u'relaxing',
            # u'sleep',
            # u'sour',
            # u'strong',
            # u'sweet',
            u'time']

    # ESW3 = ['bud',
    #         'definitely',
    #      u'feel': 20,
    #      u'flavor': 1,
    #      u'get': 20,
    #      u'got': 2,
    #      u'ha': 1,
    #      u'hit': 1,
    #      u'indica': 12,
    #      u'kush': 2,
    #      u'make': 12,
    #      u'og': 1,
    #      u'one': 20,
    #      u'purple': 2,
    #      u'sativa': 9,
    #      u'smoked': 2,
    #      u'strawberry': 1,
    #      u'wa': 20})

    ESW4 = ['weed', 'wa', 'well', 'white', 'widow', 'would', 'tasty', 'top', 'stuff', 'super', 'still', 'smooth', 'smoked',
            'smoking', 'shit', 'sativa', 'right', 'relaxed', 'recommend', 'purple', 'pretty', 'og', 'one', 'perfect',
            'far', 'feel', 'feeling', 'first', 'flavor', 'long', 'made', 'make', 'mellow', 'much', 'night', 'little', 'kush',
            'jack', 'indica', 'hybrid', 'hit', 'help', 'heavy', 'headband', 'haze', 'ha', 'gsc', 'green', 'got', 'go', 'give',
            'get', 'gdp', 'ever', 'always', 'atf', 'awesome', 'beautiful', 'bit', 'bubba', 'bud', 'buzz', 'chemdawg',
            'crack', 'definitely', 'effect']

    ESW5 = ['felt', 'also', 'try', 'hard', 'around']

    ESW6 = ['way', 'say', 'bad', 'lot', 'tried', 'though', 'flower', 'want', 'use', 'tried', 'better',
            'even', 'last', 'put']

    stops = set(list(stopwords.words('english'))) | set(
        EXTRA_STOP_WORDS) | set(ESW2) | set(ESW4) | set(ESW5) | set(ESW6)

    return stops


def clean_article(article):
    nlp = spacy.load('en')

    # Create custom stoplist
    STOPLIST = set(stopwords.words(
        'english') + ["n't", "'s", "'m", "ca", "'", "'re"] + list(ENGLISH_STOP_WORDS))
    PUNCT_DICT = {
        ord(punc): None for punc in string.punctuation if punc not in ['_', '*']}

    doc = nlp(article)

    # Let's merge all of the proper entities
    for ent in doc.ents:
        if ent.root.tag_ != 'DT':
            ent.merge(ent.root.tag_, ent.text, ent.label_)
        else:
            # Keep entities like 'the New York Times' from getting dropped
            ent.merge(ent[-1].tag_, ent.text, ent.label_)

    # Part's of speech to keep in the result
    pos_lst = ['ADJ', 'ADV', 'NOUN', 'PROPN', 'VERB']  # NUM?

    tokens = [token.lemma_.lower().replace(' ', '_')
              for token in doc if token.pos_ in pos_lst]

    # .translate(PUNCT_DICT)
    return ' '.join(token for token in tokens if token not in STOPLIST).replace("'s", '')


def get_top_words(df, num_words='all'):
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
    if num_words == 'all':
        return vect_words[sort_idxs], avg_vects[sort_idxs]

    return vect_words[sort_idxs][:num_words], avg_vects[sort_idxs][:num_words]


def get_top_words_lemmatize(df, num_words='all', ngram_range=(1, 1), max_df=0.75):
    '''
    gets top words from tfidf vectorization of reviews in dataframe df
    lemmatizes using

    input:
    df -- dataframe with 'review' column
    num_words -- number of top words to return (ranked by tfidf)

    output:
    list of top words ranked in order
    '''
    lemmatizer = WordNetLemmatizer()
    stops = get_stopwords()
    reviews = df['review'].map(lambda x: ' '.join(
        [lemmatizer.lemmatize(w) for w in x.split()])).values
    reviews = [s.encode('ascii', errors='ignore') for s in reviews]
    reviews = [re.sub('\d*', '', r) for r in reviews]

    tfvect = TfidfVectorizer(
        stop_words=stops, max_df=max_df, min_df=5, ngram_range=ngram_range)
    review_vects = tfvect.fit_transform(reviews)
    vect_words = np.array(tfvect.get_feature_names())
    review_vects = review_vects.toarray()
    avg_vects = review_vects.mean(axis=0)
    sort_idxs = np.array(np.argsort(avg_vects))[::-1]

    if num_words == 'all':
        return vect_words[sort_idxs], avg_vects[sort_idxs], review_vects

    return vect_words[sort_idxs][:num_words], avg_vects[sort_idxs][:num_words]

    ''' for 20 groups, this came up:
    ({u'body': 19,
         u'bud': 20,
         u'cheese': 2,
         u'day': 19,
         u'definitely': 14,
         u'feel': 20,
         u'flavor': 1,
         u'get': 20,
         u'got': 2,
         u'ha': 1,
         u'hit': 1,
         u'indica': 12,
         u'kush': 2,
         u'make': 12,
         u'og': 1,
         u'one': 20,
         u'purple': 2,
         u'sativa': 9,
         u'smoked': 2,
         u'strawberry': 1,
         u'wa': 20})
    '''


def lemmatize_tfidf(df, ngram_range=(1, 1), max_df=0.75, stops='all', max_features=None):
    '''
    gets top words from tfidf vectorization of reviews in dataframe df
    lemmatizes

    input:
    df -- dataframe with 'review' column
    num_words -- number of top words to return (ranked by tfidf)

    output:
    list of top words ranked in order
    '''
    lemmatizer = WordNetLemmatizer()
    if stops=='all':
        stops = get_stopwords()
    elif stops=='english':
        stops = stopwords.words('english')

    reviews = df['review'].map(lambda x: ' '.join(
        [lemmatizer.lemmatize(w) for w in x.split()])).values
    reviews = [s.encode('ascii', errors='ignore') for s in reviews]
    reviews = [re.sub('\d*', '', r) for r in reviews]

    tfvect = TfidfVectorizer(
        stop_words=stops, max_df=max_df, min_df=5, ngram_range=ngram_range, max_features=max_features)
    review_vects = tfvect.fit_transform(reviews)
    vect_words = np.array(tfvect.get_feature_names())
    review_vects = review_vects.toarray()
    avg_vects = review_vects.mean(axis=0)
    sort_idxs = np.array(np.argsort(avg_vects))[::-1]

    return tfvect, vect_words, review_vects


def get_top_bigrams(df, num_words='all'):
    '''
    gets top words from tfidf vectorization of reviews in dataframe df

    input:
    df -- dataframe with 'review' column
    num_words -- number of top words to return (ranked by tfidf), 'all' returns
    well...all words

    output:
    list of top words ranked in order
    '''
    stops = get_stopwords()
    reviews = df['review'].values
    reviews = [s.encode('ascii', errors='ignore') for s in reviews]

    tfvect = TfidfVectorizer(stop_words=stops, max_df=0.5,
                             min_df=5, ngram_range=(2, 2))
    review_vects = tfvect.fit_transform(reviews)
    vect_words = np.array(tfvect.get_feature_names())
    review_vects = review_vects.toarray()
    avg_vects = review_vects.mean(axis=0)
    sort_idxs = np.array(np.argsort(avg_vects))[::-1]
    if num_words == 'all':
        return vect_words[sort_idxs], avg_vects[sort_idxs]

    return vect_words[sort_idxs][:num_words], avg_vects[sort_idxs][:num_words]


def get_product_word_choices():
    '''
    returns list of words that can be used as choices in initialization function
    for recommendations for someone without any reviews

    these words were hand-picked from the top tfidf words from the MF product groups

    gets words for different categories (keys of a dict) that users can choose
    to have a strain recommended to them
    '''
    # couch lock was in every document with bigrams, so was 'long lasting'
    # with max_df=0.75
    word_dict = {}
    word_dict['feelings'] = ['uplifting',
                             'mellow',
                             'euphoric',
                             'euphoria',
                             'energy',
                             'energetic',
                             'relief',
                             'clear headed']
    word_dict['taste'] = ['potent',
                          'pineapple',
                          'orange',
                          'lemon',
                          'earthy',
                          'diesel',
                          'blackberry',
                          'blueberry',
                          'cherry',
                          'banana',
                          'fruity pebbles',
                          'juicy fruit']
    word_dict['conditions'] = ['insomnia',
                               'stress',
                               'headache',
                               'depression',
                               'anxiety']
    word_dict['effects'] = ['body',
                            'couch',
                            'mellow',
                            'focus',
                            'focused',
                            'cerebral',
                            'body buzz',
                            'couch lock',
                            'long lasting']
    word_dict['times'] = ['daytime',
                          'night',
                          'wake bake']

    return word_dict


def get_user_word_choices():
    '''
    returns list of words that can be used as choices in initialization function
    for recommendations for someone without any reviews

    these words were hand-picked from the top tfidf words from the MF user groups

    gets words for different categories (keys of a dict) that users can choose
    to have a strain recommended to them
    '''
    # couch lock was in every document with bigrams, so was 'long lasting'
    # with max_df=0.75
    word_dict = {}
    word_dict['feelings'] = ['uplifting',
                             'mellow',
                             'euphoric',
                             'euphoria',
                             'energy',
                             'energetic',
                             'relief',
                             'clear headed',
                             'relaxing',
                             'chill']

    word_dict['taste'] = ['potent',
                          'pineapple',
                          'orange',
                          'lemon',
                          'earthy',
                          'diesel',
                          'blackberry',
                          'blueberry',
                          'cherry',
                          'banana',
                          'fruity pebbles',
                          'juicy fruit',
                          'fruity',
                          'sweet',
                          'light',
                          'grape',
                          'cheese'
                          ]

    word_dict['conditions'] = ['insomnia',
                               'stress',
                               'headache',
                               'depression',
                               'anxiety',
                               'pain'
                               'back pain'] # need to translate this to 'back'

    word_dict['effects'] = ['body',
                            'couch',
                            'mellow',
                            'focus',
                            'focused',
                            'cerebral',
                            'body buzz',
                            'couch lock',
                            'long lasting',
                            'strong',
                            'head',
                            'relaxing',
                            'sleep',
                            'couch',
                            'energetic']

    word_dict['times'] = ['daytime',
                          'night',
                          'wake bake',
                          'day']

    return word_dict


def check_word_choices_in_topwords(word_dict, prod_top_words):
    '''
    checks to make sure each word in the word_dict is in prod_top_words

    returns list of words not in the top_words, but in the word_dict
    '''
    pass


def get_sents_with_sleep(df):
    '''
    takes dataframe with reviews and product names and returns dataframe with
    sentence with sleep appended
    '''
    # first ensure that our indices aren't going to screw things up
    new_df = df.copy()
    new_df = new_df.reset_index(drop=True)
    new_df['sleep_sentence'] = [[] for i in range(new_df.shape[0])]
    new_df['sent_count'] = 0
    punct_no_per = re.sub('\.', '', string.punctuation)
    for i, r in new_df.iterrows():
        print i, new_df.shape[0]
        sentences = []
        scount = 0
        sents = list(parser(r['review']).sents)
        for s in sents:
            s = s.string.strip()
            res = re.search('.*sleep.*', s, re.IGNORECASE)
            if res:
                sentences.append(res.group(0))
                scount += 1

        new_df.set_value(i, 'sleep_sentence', sentences)
        new_df.set_value(i, 'sent_count', scount)

    return new_df


def get_sents_with_words(df, word):
    '''
    takes dataframe with reviews and product names and returns dataframe with
    sentence with 'word' appended
    '''
    # first ensure that our indices aren't going to screw things up
    new_df = df.copy()
    new_df = new_df.reset_index(drop=True)
    new_df['word_sentence'] = [[] for i in range(new_df.shape[0])]
    new_df['sent_count'] = 0
    punct_no_per = re.sub('\.', '', string.punctuation)
    for i, r in new_df.iterrows():
        #print i, new_df.shape[0]
        sentences = []
        scount = 0
        sents = list(parser(r['review']).sents)
        for s in sents:
            s = s.string.strip()
            res = re.search('.*' + word + '.*', s, re.IGNORECASE)
            if res:
                sentences.append(res.group(0))
                scount += 1

        new_df.set_value(i, 'word_sentence', sentences)
        new_df.set_value(i, 'sent_count', scount)

    return new_df


if __name__=="__main__":
    prod_group_dfs, user_group_dfs = load_group_dfs()
    df = dp.load_data()
    sent_df = get_sents_with_sleep(df)
    sent_df.to_csv('leafly/sleep_sentence_df.csv')
    #
    # prod_group_sleep_dfs = {}
    # test_w_sent = test[test['sent_count'] > 0]
