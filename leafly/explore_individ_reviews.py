import pandas as pd
from pymongo import MongoClient
import numpy as np
import leafly.data_preprocess as dp

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


effect_df = pd.DataFrame(effect_dict, dtype='float64')
ohe_df = full_df.merge(effect_df, on='link')
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

# now try clustering by this normalized shit
cluster_data = prod_ohe[list(unique_effects)].values
names = prod_ohe.index.values
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import time
from sklearn.decomposition import PCA
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


import plotly.graph_objs as go
import plotly.plotly as py
from plotly.graph_objs import XAxis, YAxis, ZAxis, Layout, Scene
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
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


# check out users with more than 10 reviews, and not anonymous
user_group = full_df.groupby('user').count()
# about 42k with more than 10 reviews, 67 with more than 52
top_users = set(user_group[user_group['full_review'] >= 5].index.values)
top_df = full_df[full_df['user'].isin(top_users)]
top_df = top_df[top_df['user'] != 'Anonymous']

# dropped a few
top_df.drop_duplicates(subset=[u'product', u'rating', u'full_review', u'user'])
