import leafly.search_for_words as sfw
import leafly.nlp_funcs as nl
import leafly.data_preprocess as dp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

df, prod_review_df = sfw.load_data()

tfvect, vect_words, review_vects = nl.lemmatize_tfidf(prod_review_df)

km = KMeans(n_clusters=10, n_jobs=-1, random_state=42)
km.fit(review_vects)
