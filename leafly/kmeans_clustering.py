import time
from sklearn.decomposition import PCA
import leafly.search_for_words as sfw
import leafly.nlp_funcs as nl
import leafly.data_preprocess as dp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import plotly.graph_objs as go
import plotly.plotly as py
from plotly.graph_objs import XAxis, YAxis, ZAxis, Layout, Scene
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from sklearn.metrics import silhouette_score

df, prod_review_df = sfw.load_data()

tfvect, vect_words, review_vects = nl.lemmatize_tfidf(prod_review_df, max_features=1000, ngram_range=(1, 2))
pca_r= PCA(n_components=200)
review_pca = pca_r.fit_transform(review_vects)

num_kmeans = 15
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

data = go.Scatter(
        x=range(2, num_kmeans),
        y=scores,
        mode='markers',
        marker=dict(
            size=12,
            line=dict(
                color='rgba(217, 217, 217, 0.14)',
                width=0.5
            ),
            opacity=0.8
        )
    )

layout = Layout(
    title='kmeans plot strains',
    scene=Scene(
        xaxis=XAxis(title='number of KMeans clusters'),
        yaxis=YAxis(title='sum of squared distances from datapoints to cluster centers')
    )
)

py.plot([data], layout=layout, filename='kmeans-scatter', world_readable=True)

# look at silhouette_score
sil_scores = []
for km in kmeanses:
    labels = km.labels_
    sil_scores.append(silhouette_score(review_vects, labels, metric='euclidean'))

# shit...looks like 2 clusters is best, with 200 or full tfidf
plt.scatter(range(2, num_kmeans), sil_scores)
plt.show()


# adapted from plotly and SO
# http://stackoverflow.com/questions/26941135/show-legend-and-label-axes-in-plotly-3d-scatter-plots
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



####################


num_kmeans = 15
kmeanses = []
scores = []
start = time.time()
for i in range(2, num_kmeans):
    km = KMeans(n_clusters=i, n_jobs=-1, random_state=42)
    kmeanses.append(km)
    km.fit(review_vects)
    scores.append(-km.score(review_vects)) # withi-cluster sum of squares

endTime = time.time()
print 'took', endTime - start, 'seconds'

data = go.Scatter(
        x=range(2, num_kmeans),
        y=scores,
        mode='markers',
        marker=dict(
            size=12,
            line=dict(
                color='rgba(217, 217, 217, 0.14)',
                width=0.5
            ),
            opacity=0.8
        )
    )

layout = Layout(
    title='kmeans plot strains',
    scene=Scene(
        xaxis=XAxis(title='number of KMeans clusters'),
        yaxis=YAxis(title='sum of squared distances from datapoints to cluster centers')
    )
)

py.plot([data], layout=layout, filename='kmeans-scatter', world_readable=True)

# look at silhouette_score
sil_scores = []
for km in kmeanses:
    labels = km.labels_
    sil_scores.append(silhouette_score(review_vects, labels, metric='euclidean'))

# shit...looks like 2 clusters is best, with 200 or full tfidf
plt.scatter(range(2, num_kmeans), sil_scores)
plt.show()

# lets look at the clusters
# adapted from plotly and SO
# http://stackoverflow.com/questions/26941135/show-legend-and-label-axes-in-plotly-3d-scatter-plots
cur_km = kmeanses[8]
traces = []
for i in range(10):
    x, y, z = bio_PCA_sc[cur_km.labels_ == i, 0], bio_PCA_sc[cur_km.labels_ == i, 1], bio_PCA_sc[cur_km.labels_ == i, 3]
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
    title='10 KMeans clusters of MBMS raw biomass',
    scene=Scene(
        xaxis=XAxis(title='PCA Dimension 1'),
        yaxis=YAxis(title='PCA Dimension 2'),
        zaxis=ZAxis(title='PCA Dimension 3')
    )
)

fig = go.Figure(data=traces, layout=layout)
py.plot(fig, filename='2 kmeans clusters of strains', world_readable=True)



km2 = kmeanses[0]
labels = km2.labels_
group0 = prod_review_df[labels == 0]
group1 = prod_review_df[labels == 1]
tfvect0, vect_words0, review_vects0 = nl.lemmatize_tfidf(group0, max_features=200)

# lets try clustering within a cluster and see how it looks
num_kmeans = 50
kmeanses0 = []
scores0 = []
start = time.time()
for i in range(2, num_kmeans):
    km = KMeans(n_clusters=i, n_jobs=-1, random_state=42)
    kmeanses0.append(km)
    km.fit(review_vects0)
    scores0.append(-km.score(review_vects)) # withi-cluster sum of squares

endTime = time.time()
print 'took', endTime - start, 'seconds'

# look at silhouette_score
sil_scores0 = []
for km in kmeanses0:
    labels = km.labels_
    sil_scores0.append(silhouette_score(review_vects0, labels, metric='euclidean'))


# 15 clusters looks best
f = plt.figure()
ax = f.add_subplot(1, 1, 1)
ax.scatter(range(2, num_kmeans), sil_scores0)
ax.set_title('group0 clusters')
plt.show()



# now the second cluster
tfvect1, vect_words1, review_vects1 = nl.lemmatize_tfidf(group1, max_features=200)

num_kmeans = 50
kmeanses1 = []
scores1 = []
start = time.time()
for i in range(2, num_kmeans):
    km = KMeans(n_clusters=i, n_jobs=-1, random_state=42)
    kmeanses1.append(km)
    km.fit(review_vects1)
    scores1.append(-km.score(review_vects)) # withi-cluster sum of squares

endTime = time.time()
print 'took', endTime - start, 'seconds'

# look at silhouette_score
sil_scores1 = []
for km in kmeanses1:
    labels = km.labels_
    sil_scores1.append(silhouette_score(review_vects1, labels, metric='euclidean'))


# 7 clusters looks best for this one
f = plt.figure()
ax = f.add_subplot(1, 1, 1)
ax.scatter(range(2, num_kmeans), sil_scores1)
ax.set_title('group1 clusters')
plt.show()
