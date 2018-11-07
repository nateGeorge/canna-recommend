import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle as pk
import plotly.plotly as py
import plotly.graph_objs as go
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import time
from sklearn.decomposition import PCA
import plotly.plotly as py
from plotly.graph_objs import XAxis, YAxis, ZAxis, Layout, Scene
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

all_df = pd.read_pickle('analytical360/data_df_11-13-2016.pk')
leaf_df = pd.read_pickle('analytical360/leafly_matched_df_11-13-2016.pk')

product_chem_df = leaf_df.groupby('name').mean()
product_chem_df.drop('mask', axis=1, inplace=True)
product_chem_df.drop('isedible', axis=1, inplace=True)

# for c in product_chem_df.columns:
#     product_chem_df[c].hist(bins=50)
#     plt.title(c)
#     plt.show()

groups = pk.load(open('analytical360/3_kmeans_chem_groups_pd.pk'))
# make figs of distibutions of thc, cbd, and some other few terps here
plt.rcParams.update({'font.size': 18})
colors = ['m', 'g', 'b']
for c in product_chem_df.columns:
    #f = plt.figure(figsize=(20, 8))
    #plt.title(c)
    for i in range(3):
        # normalize histogram so they all have the same max
        tempdata = groups[i][c].values
        plt.hist(tempdata, bins=50, alpha=0.5, label='group' + str(i), normed=True, color=colors[i])
    plt.xlabel('% ' + c)
    plt.legend()
    # plt.tight_layout()
    plt.show()


for c in product_chem_df.columns:
    f = plt.figure(figsize=(20, 8))
    plt.title(c)
    traces = []
    for i in range(3):
        traces.append(go.Histogram(
        x=groups[i][c].values,
        opacity=0.55,
        histnorm='probability',
        name='group ' + str(i),
        nbinsx=50
        ))
    layout = go.Layout(
        title=c,
        barmode='overlay'
    )
    fig = go.Figure(data=traces, layout=layout)
    py.plot(fig)


# try clustering all the data to see how it looks
all_df = pd.read_pickle('analytical360/data_df_11-13-2016.pk') # dataframe with all chem data
product_chem_df = all_df.groupby('name').mean()
product_chem_df.drop('mask', axis=1, inplace=True)
product_chem_df.drop('isedible', axis=1, inplace=True)
# impute missing values with means`
for c in product_chem_df.columns:
    product_chem_df[c].fillna(value=product_chem_df[c].mean(), inplace=True)

#############################################################
# try clustering stuff
cluster_data = product_chem_df.values
names = product_chem_df.index.values
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
print('took', endTime - start, 'seconds')

plt.scatter(list(range(2, num_kmeans)), sil_scores)
plt.show()

plt.scatter(list(range(2, num_kmeans)), scores)
plt.show()

pca= PCA(n_components=10)
chem_pca = pca.fit_transform(cluster_data)

cur_km = kmeanses[1]
traces = []
for i in range(3):
    print('group', i, chem_pca[cur_km.labels_ == i, 0].shape)
    x, y, z = chem_pca[cur_km.labels_ == i, 0], chem_pca[cur_km.labels_ == i, 1], chem_pca[cur_km.labels_ == i, 3]
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
    title='3 KMeans clusters of strains by chemistry',
    scene=Scene(
        xaxis=XAxis(title='PCA Dimension 1'),
        yaxis=YAxis(title='PCA Dimension 2'),
        zaxis=ZAxis(title='PCA Dimension 3')
    )
)

fig = go.Figure(data=traces, layout=layout)
py.plot(fig, filename='3 KMeans clusters of strains by chemistry', world_readable=True)

groups = []
for i in range(3):
    groups.append(product_chem_df[cur_km.labels_ == i])
    print(groups[i].mean())

for c in product_chem_df.columns:
    #f = plt.figure(figsize=(20, 8))
    #plt.title(c)
    for i in range(3):
        # normalize histogram so they all have the same max
        tempdata = groups[i][c].values
        plt.hist(tempdata, bins=50, alpha=0.5, label='group' + str(i), normed=True, color=colors[i])
    plt.xlabel('% ' + c)
    plt.legend()
    # plt.tight_layout()
    plt.show()
