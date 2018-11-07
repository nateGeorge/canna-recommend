import leafly.search_for_words as sfw
import leafly.nlp_funcs as nl
import leafly.explore_individ_reviews as eir
import pandas as pd
import numpy as np
from scipy import spatial
from fancyimpute import BiScaler, KNN, NuclearNormMinimization, SoftImpute
from sklearn.preprocessing import StandardScaler
import os
import pickle as pk

# tf-idf similarity
review_vects_file = 'leafly/review_vects_full.pk'
review_vects2_file = 'leafly/review_vects2_full.pk'
dist_file1 = 'leafly/review_tfidf_dists1.pk'
dist_file2 = 'leafly/review_tfidf_dists2.pk'
vect_words1_file = 'leafly/vect_words1.pk'
vect_words2_file = 'leafly/vect_words2.pk'
strain_name_file = 'leafly/tfidf_strain_names.pk'
if os.path.exists(dist_file1):
    tfidf_dists1 = pk.load(dist_file1)
    tfidf_dists2 = pk.load(dist_file2)
    # review_vects = pd.read_pickle(review_vects_file)
    # review_vects2 = pd.read_pickle(review_vects2_file)
else:
    df, prod_review_df = sfw.load_data(full=True)
    tfvect, vect_words, review_vects = nl.lemmatize_tfidf(prod_review_df, max_features=1000, ngram_range=(1, 2))
    tfvect2, vect_words2, review_vects2 = nl.lemmatize_tfidf(prod_review_df, max_features=1000, ngram_range=(2, 2))
    review_vects = pd.DataFrame(review_vects)
    review_vects2 = pd.DataFrame(review_vects2)
    names = prod_review_df['product'].values
    pk.dump(names, open(strain_name_file, 'w'), 2)
    # pre-compute distances for efficiency
    dist_list = []
    for i in range(review_vects.shape[0]):
        print(i)
        dists = []
        for j in range(review_vects.shape[0]):
            dists.append(spatial.distance.cosine(review_vects[j], review_vects[i]))

        dist_list.append(dists)

    dist_list2 = []
    for i in range(review_vects2.shape[0]):
        print(i)
        dists = []
        for j in range(review_vects2.shape[0]):
            dists.append(spatial.distance.cosine(review_vects2[j], review_vects2[i]))

        dist_list2.append(dists)

    pk.dump(dist_list, open(dist_file1, 'w'), 2)
    pk.dump(dist_list2, open(dist_file2, 'w'), 2)
    pk.dump(vect_words, open(vect_words1_file, 'w'), 2)
    pk.dump(vect_words2, open(vect_words2_file, 'w'), 2)
    pk.dump(review_vects, open(review_vects_file, 'w'), 2)
    pk.dump(review_vects2, open(review_vects2_file, 'w'), 2)

def get_tfidf_sims(strain, names, dist_list, dist_list2, mix_factor = 0.8):
    '''
    uses pre-computed lists of cosine distances of products to calculate
    most similar strains

    args:
    strain -- (string) name of strain to search for close relatives
    names -- (list) list of strain names with same indexing as dist_lists
    dist_list, dist_list2: (lists) lists of cosine distances
    of tf-idf vectors from full reviews
    mix_factor -- (float) value for % of final result due to dist_list vs
    dist_list2
    '''
    names = list(names)
    idx = names.index(strain)
    dists1 = np.array(dist_list[idx])
    dists2 = np.array(dist_list2[idx])
    dist_avg = dists1 * mix_factor + dists2 * (mix_factor - 1)

    return dist_avg

# testing tfidf sims func
testStr = names[100]
dist_avg = get_tfidf_sims(testStr, names, dist_list, dist_list2)
sorted_idxs = np.argsort(dist_avg)
names[sorted_idxs[:10]]




# effects similarity
ohe_file = 'leafly/prod_ohe.pk'
if os.exists(ohe_file):
    prod_ohe = pd.read_pickle(ohe_file)
else:
    ohe_df, prod_ohe = eir.load_all_full_reviews()
    prod_ohe.to_pickle(ohe_file)

prod_ohe.drop('isok', axis=1, inplace=True)
prod_ohe.drop('rating', axis=1, inplace=True)

unique_effects = pk.load(open('leafly/unique_effects.pk'))
effects_df = prod_ohe[list(unique_effects)]


# flavors similarity
unique_flavors = pk.load(open('leafly/unique_flavors.pk'))
flavors_df = prod_ohe[list(unique_flavors)]

# chemistry similarity
def get_chem_df():
    '''
    retrieves, cleans dataframe of chemistry data for strains in leafly
    '''
    chem_df_file = 'analytical360/scealed_leaf_chem.pk'
    if os.path.exists(chem_df_file):
        scaled_leaf_chem = pd.read_pickle(chem_df_file)
    else:
        leaf_df = pd.read_pickle('analytical360/leafly_matched_df_11-13-2016.pk')
        leaf_df.drop('mask', axis=1, inplace=True)
        leaf_df.drop('isedible', axis=1, inplace=True)
        leaf_df.drop('filename', axis=1, inplace=True)
        leaf_df.drop('clean_name', axis=1, inplace=True)
        # unfortunately need to drop a few terps because too much nan
        # dropping anything with less than 75% non-nan in leaf_prod_chem
        leaf_df.drop('Terpinolene', axis=1, inplace=True)
        leaf_df.drop('cbg', axis=1, inplace=True)
        leaf_df.drop('cbn', axis=1, inplace=True)
        leaf_df.drop('Limonene', axis=1, inplace=True)
        leaf_df.drop('Linalool', axis=1, inplace=True)
        leaf_df.drop('caryophyllene_oxide', axis=1, inplace=True)


        # impute missing values with means`
        # skip_cols = set(['name'])
        # for c in leaf_df.columns:
        #     if c not in skip_cols:
        #         leaf_df[c].fillna(value=leaf_df[c].mean(), inplace=True)

        # impute missing values with knn
        leaf_df_vals = leaf_df.drop('name', axis=1).values
        leaf_df_filled = KNN(k=6).complete(leaf_df_vals)

        cols = list(leaf_df.columns.values)
        cols.remove('name')
        new_leaf_df = pd.DataFrame(columns=cols, data=leaf_df_filled)
        new_leaf_df['name'] = leaf_df['name'].values

        leaf_prod_chem = new_leaf_df.groupby('name').mean()
        # need to normalize data a bit...thc/cbd should still have the highest influence,
        # but only by a factor of 3 (arbitrary choice)
        scaled_leaf_chem = leaf_prod_chem.copy()
        scalers = []
        for c in scaled_leaf_chem.columns:
            sc = StandardScaler()
            scalers.append(sc)
            scaled_leaf_chem[c] = sc.fit_transform(scaled_leaf_chem[c])

        scaled_leaf_chem['thc_total'] = scaled_leaf_chem['thc_total'] * 3
        scaled_leaf_chem['cbd_total'] = scaled_leaf_chem['cbd_total'] * 3

        scaled_leaf_chem.to_pickle(chem_df_file)

    return scaled_leaf_chem

def test_chem_sim(scaled_leaf_chem):
    testStr = scaled_leaf_chem.iloc[666].name
    testVect = scaled_leaf_chem.ix[testStr].values

    dists = []
    for i, r in scaled_leaf_chem.iterrows():
        dists.append(spatial.distance.cosine(testVect, r.values))

    # the lowest numbers are the closest distance (most similar) so we keep numpy's
    # default sorting (low->high)
    # of course it's most similar to itself, so need to exclude first result
    chem_dists = np.argsort(dists)




# this is for ALL strains from the chem DB
all_df = pd.read_pickle('analytical360/data_df_11-13-2016.pk')
all_df.drop('mask', axis=1, inplace=True)
all_df.drop('isedible', axis=1, inplace=True)
all_df.drop('filename', axis=1, inplace=True)
all_prod_chem = all_df.groupby('clean_name').mean()
testStr = all_df['clean_name'].iloc[666]

testVect = all_df[all_df['clean_name'] == testStr]

def calc_sim(scaled_leaf_chem):
    testStr = scaled_leaf_chem.iloc[666].name
    testVect = scaled_leaf_chem.ix[testStr].values

    dists = []
    for i, r in scaled_leaf_chem.iterrows():
        dists.append(spatial.distance.cosine(testVect, r.values))

    # the lowest numbers are the closest distance (most similar) so we keep numpy's
    # default sorting (low->high)
    # of course it's most similar to itself, so need to exclude first result
    chem_dists = np.argsort(dists)
    return chem_dists
