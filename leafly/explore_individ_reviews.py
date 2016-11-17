import pandas as pd
from pymongo import MongoClient
import numpy as np
import leafly.data_preprocess as dp
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import time
from sklearn.decomposition import PCA
import plotly.graph_objs as go
import plotly.plotly as py
from plotly.graph_objs import XAxis, YAxis, ZAxis, Layout, Scene
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import leafly.search_for_words as sfw


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

    orig_df = dp.load_data(no_anon=False, get_links=True)

    full_df = full_rev_df.merge(orig_df, on='link')

    # one-hot encode effects
    unique_effects = set(np.unique(effects_list))
    pk.dump(unique_effects, open('leafly/unique_effects.pk', 'w'), 2)
    effect_dict = {}
    for i, r in full_df.iterrows():
        temp_ef = set()
        if r['effects'] != '':
            temp_ef = set([s.strip() for s in r['effects'].split('-')])
            if '' in temp_ef:
                print r
                break
            for e in temp_ef:
                effect_dict.setdefault(e, []).append(1)
        for e in unique_effects.difference(temp_ef):
            effect_dict.setdefault(e, []).append(0)

    effect_dict['link'] = full_df['link'].values
    # check to make sure lengths are the same
    for k in effect_dict.keys():
        print k, len(effect_dict[k])

    # one-hot encode flavors
    unique_flavors = set(np.unique(flavors_list))
    pk.dump(unique_flavors, open('leafly/unique_flavors.pk', 'w'), 2)
    flavor_dict = {}
    for i, r in full_df.iterrows():
        temp_fl = set()
        if r['flavors'] != '':
            temp_fl = set([s.strip() for s in r['flavors'].split('-')])
            if '' in temp_fl:
                print r
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
        print sumcount

    for i, r in prod_ohe.iterrows():
        sumcount = np.sum([r[c] for c in unique_flavors])
        if sumcount == 0:
            continue
        for c in unique_flavors:
            prod_ohe = prod_ohe.set_value(i, c, r[c] / float(sumcount))

        sumcount = np.sum([r[c] for c in unique_flavors])
        print sumcount

    return ohe_df, prod_ohe

def cluster_by_effects_flavors():
    '''
    '''
    # now try clustering by this normalized shit
    cluster_data = prod_ohe[list(unique_effects)].values
    names = prod_ohe.index.values
    num_kmeans = 15
    kmeanses = []
    scores = []
    sil_scores = []
    start = time.time()
    for i in range(2, num_kmeans):
        km = KMeans(n_clusters=i, n_jobs=-1, random_state=42)
        kmeanses.append(km)
        km.fit(cluster_data)
        scores.append(-km.score(cluster_data)) # withi-cluster sum of squares
        labels = km.labels_
        sil_scores.append(silhouette_score(cluster_data, labels, metric='euclidean'))

    endTime = time.time()
    print 'took', endTime - start, 'seconds'

    plt.scatter(range(2, num_kmeans), sil_scores)
    plt.show()

    plt.scatter(range(2, num_kmeans), scores)
    plt.show()

    pca= PCA(n_components=10)
    effects_pca = pca.fit_transform(cluster_data)

    cur_km = kmeanses[1]
    traces = []
    for i in range(3):
        print 'group', i, effects_pca[cur_km.labels_ == i, 0].shape
        x, y, z = effects_pca[cur_km.labels_ == i, 0], effects_pca[cur_km.labels_ == i, 1], effects_pca[cur_km.labels_ == i, 3]
        traces.append(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers',
            marker=dict(
                size=6,
    #             line=dict(
    #                 color='rgba(217, 217, 217, 0.14)',
    #                 width=0.2
    #             ),
                opacity=0.5
            ),
            name='cluster ' + str(i),
            text=names[cur_km.labels_ == i]
        ))


    layout = Layout(
        title='3 KMeans clusters of strains by effects',
        scene=Scene(
            xaxis=XAxis(title='PCA Dimension 1'),
            yaxis=YAxis(title='PCA Dimension 2'),
            zaxis=ZAxis(title='PCA Dimension 3')
        )
    )

    fig = go.Figure(data=traces, layout=layout)
    py.plot(fig, filename='3 KMeans clusters of strains by effects', world_readable=True)

    # now lets see what the themes of the three groups are
    for i in range(3):
        group = prod_ohe[cur_km.labels_ == i]
        sorted_effects = []
        for e in unique_effects:
            sorted_effects.append((e, group[e].mean()))

        sorted_effects = sorted(sorted_effects, key=lambda x: x[1], reverse=True)
        print 'group', i
        print sorted_effects
        for e in sorted_effects:
            print e[0]
        print ''
        print ''

    '''
    group 0:
    Happy
    Uplifted
    Euphoric
    Relaxed
    Creative
    Energetic
    Focused
    Dry Mouth

    group 1:
    Dry Mouth
    Dizzy
    Hungry
    Paranoid
    Anxious
    Dry Eyes
    Uplifted

    group 2:
    Relaxed
    Happy
    Euphoric
    Sleepy
    Uplifted
    Hungry
    Dry Mouth
    '''

    group1 = prod_ohe[cur_km.labels_ == 1]
    # holy shit stay away from bhang!
    for i in group1.index:
        print i

    bad = group1.index.values

    '''
    aberdeen
    als-dream
    bhang-bubble-gum
    bhang-casey-jones
    bhang-darth-vader-og
    bhang-jack-frost
    bhang-jack-herer
    bhang-lambs-bread
    bhang-master-kush
    bhang-og-kush
    bhang-trainwreck
    bhang-white-widow
    bhang-yoda-og
    blue-nina
    bob-saget
    citrus-punch
    colorado-clementines
    critters-cookies
    deadwood
    dixie-elixirs-lemonade
    dixie-elixirs-mixed-berry
    dixie-elixirs-sweet-tea
    dixie-medicated-fruit-lozenges
    dizzy-og
    dougs-varin
    edi-pure-strawberry-belts
    flo-walker
    future
    g-stik-rosado
    golden-xtrx-personal-vaporizer-hybrid
    grilled-cheese
    hawaiian-sunrise
    heaven-scent
    kali-47
    kaptns-grand-dream
    la-nina
    la-sunshine
    liquid-gold-vape-pen-red-diesel
    little-devil
    little-dragon
    madzilla
    majestic-12
    moondance
    nepalese-jam
    ogre-berry
    pink-berry
    poochie-love
    purple-aurora
    purple-pantera
    rebel-god-smoke
    redd-cross
    south-indian-indica
    tigermelon
    wmd
    '''

    # same thing for flavors
    cluster_data = prod_ohe[list(unique_effects)].values
    names = prod_ohe.index.values
    num_kmeans = 6
    kmeanses = []
    scores = []
    sil_scores = []
    start = time.time()
    for i in range(2, num_kmeans):
        km = KMeans(n_clusters=i, n_jobs=-1, random_state=42)
        kmeanses.append(km)
        km.fit(cluster_data)
        scores.append(-km.score(cluster_data)) # withi-cluster sum of squares
        labels = km.labels_
        sil_scores.append(silhouette_score(cluster_data, labels, metric='euclidean'))

    endTime = time.time()
    print 'took', endTime - start, 'seconds'

    plt.scatter(range(2, num_kmeans), sil_scores)
    plt.show()

    plt.scatter(range(2, num_kmeans), scores)
    plt.show()

    pca= PCA(n_components=10)
    flavors_pca = pca.fit_transform(cluster_data)

    cur_km = kmeanses[1]
    traces = []
    for i in range(3):
        print 'group', i, flavors_pca[cur_km.labels_ == i, 0].shape
        x, y, z = flavors_pca[cur_km.labels_ == i, 0], flavors_pca[cur_km.labels_ == i, 1], flavors_pca[cur_km.labels_ == i, 3]
        traces.append(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers',
            marker=dict(
                size=6,
    #             line=dict(
    #                 color='rgba(217, 217, 217, 0.14)',
    #                 width=0.2
    #             ),
                opacity=0.5
            ),
            name='cluster ' + str(i),
            text=names[cur_km.labels_ == i]
        ))


    layout = Layout(
        title='3 KMeans clusters of strains by effects',
        scene=Scene(
            xaxis=XAxis(title='PCA Dimension 1'),
            yaxis=YAxis(title='PCA Dimension 2'),
            zaxis=ZAxis(title='PCA Dimension 3')
        )
    )

    fig = go.Figure(data=traces, layout=layout)
    py.plot(fig, filename='3 KMeans clusters of strains by flavors', world_readable=True)

    # now lets see what the themes of the three groups are
    for i in range(3):
        group = prod_ohe[cur_km.labels_ == i]
        sorted_flavors = []
        for e in unique_flavors:
            sorted_flavors.append((e, group[e].mean()))

        sorted_flavors = sorted(sorted_flavors, key=lambda x: x[1], reverse=True)
        print 'group', i
        print sorted_flavors
        for e in sorted_flavors:
            print e[0]
        print ''
        print ''


    '''
    group 0: citrisy pine berry
    Sweet
    Earthy
    Citrus
    Pungent
    Pine
    Berry
    Skunk
    Flowery
    Lemon
    Woody
    Diesel
    Tropical
    Spicy/Herbal
    Blueberry
    Orange

    group 1:
    Tar
    Earthy
    Cheese
    Blue Cheese
    Lemon
    Citrus
    Berry
    Menthol
    Chemical
    Ammonia
    Grape
    Peach
    Rose
    Diesel
    Pine

    group 2: sweet pine berry
    Earthy
    Sweet
    Pungent
    Berry
    Pine
    Woody
    Citrus
    Skunk
    Flowery
    Spicy/Herbal
    Lemon
    Blueberry
    Diesel
    Grape
    Tropical
    '''
    group1 = prod_ohe[cur_km.labels_ == 1]
    # holy shit stay away from bhang!
    for i in group1.index:
        print i

    bad = group1.index.values

    '''
    group1:
    aberdeen
    als-dream
    bhang-bubble-gum
    bhang-casey-jones
    bhang-darth-vader-og
    bhang-jack-frost
    bhang-jack-herer
    bhang-lambs-bread
    bhang-master-kush
    bhang-og-kush
    bhang-trainwreck
    bhang-white-widow
    bhang-yoda-og
    blue-nina
    bob-saget
    citrus-punch
    colorado-clementines
    critters-cookies
    deadwood
    dixie-elixirs-lemonade
    dixie-elixirs-mixed-berry
    dixie-elixirs-sweet-tea
    dixie-medicated-fruit-lozenges
    dizzy-og
    dougs-varin
    edi-pure-strawberry-belts
    flo-walker
    future
    g-stik-rosado
    golden-xtrx-personal-vaporizer-hybrid
    grilled-cheese
    hawaiian-sunrise
    heaven-scent
    kali-47
    kaptns-grand-dream
    la-nina
    la-sunshine
    liquid-gold-vape-pen-red-diesel
    little-devil
    little-dragon
    madzilla
    majestic-12
    moondance
    nepalese-jam
    ogre-berry
    pink-berry
    poochie-love
    purple-aurora
    purple-pantera
    rebel-god-smoke
    redd-cross
    south-indian-indica
    tigermelon
    wmd
    '''

if __name__ == "__main__":
    # check out users with more than 10 reviews, and not anonymous
    user_group = full_df.groupby('user').count()
    # about 42k with more than 10 reviews, 67 with more than 52
    top_users = set(user_group[user_group['full_review'] >= 5].index.values)
    top_df = full_df[full_df['user'].isin(top_users)]
    top_df = top_df[top_df['user'] != 'Anonymous']

    # dropped a few
    top_df.drop_duplicates(subset=[u'product', u'rating', u'full_review', u'user'])


    # cluster by tf-idf of full reviews
    # first just get tfidf vectors
    df, prod_review_df = sfw.load_data(full=True)
    tfvect, vect_words, review_vects = nl.lemmatize_tfidf(prod_review_df, max_features=1000, ngram_range=(1, 2))
    tfvect2, vect_words2, review_vects2 = nl.lemmatize_tfidf(prod_review_df, max_features=1000, ngram_range=(2, 2))

    # cluster again by full review vects
    pca_r= PCA(n_components=10)
    review_pca = pca_r.fit_transform(review_vects)

    num_kmeans = 10
    kmeanses = []
    scores = []
    sil_scores = []
    start = time.time()
    for i in range(2, num_kmeans):
        km = KMeans(n_clusters=i, n_jobs=-1, random_state=42)
        kmeanses.append(km)
        km.fit(review_pca)
        scores.append(-km.score(review_pca)) # withi-cluster sum of squares
        labels = km.labels_
        sil_scores.append(silhouette_score(review_vects, labels, metric='euclidean'))

    endTime = time.time()
    print 'took', endTime - start, 'seconds'

    # look at silhouette_score
    sil_scores = []
    for km in kmeanses:
        labels = km.labels_
        sil_scores.append(silhouette_score(review_vects, labels, metric='euclidean'))

    # shit...looks like 2 clusters is best, with 200 or full tfidf
    plt.scatter(range(2, num_kmeans), sil_scores)
    plt.show()

    cur_km = kmeanses[1]
    traces = []
    for i in range(3):
        x, y, z = review_pca[cur_km.labels_ == i, 0], review_pca[cur_km.labels_ == i, 1], review_pca[cur_km.labels_ == i, 3]
        traces.append(go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode='markers',
            marker=dict(
                size=6,
    #             line=dict(
    #                 color='rgba(217, 217, 217, 0.14)',
    #                 width=0.2
    #             ),
                opacity=0.5
            ),
            name='cluster ' + str(i)
        ))


    layout = Layout(
        title='3 KMeans clusters of strains',
        scene=Scene(
            xaxis=XAxis(title='PCA Dimension 1'),
            yaxis=YAxis(title='PCA Dimension 2'),
            zaxis=ZAxis(title='PCA Dimension 3')
        )
    )

    fig = go.Figure(data=traces, layout=layout)
    py.plot(fig, filename='3 KMeans clusters of strains', world_readable=True)

    # lets find top grams in each group
    vect_words = np.array(tfvect.get_feature_names())
    groups = []
    for i in range(3):
        names = prod_review_df[cur_km.labels_ == i]['product']
        groups.append(prod_review_df[cur_km.labels_ == i])
        words = review_vects[cur_km.labels_ == i, :]
        avg_vects = words.mean(axis=0)
        idx = np.argsort(avg_vects)[::-1]
        print 'group', i
        print zip(avg_vects[idx][:10], vect_words[idx][:10])
        print ''
        print ''
