import os
import re

import pandas as pd
import numpy as np

from sys import argv
from io import StringIO

def summarize_stats(filename):
    stats = pd.read_csv(filename)
    base, ext = os.path.splitext(filename)

    overall = stats.iloc[-1]

    n = overall['n']
    m = overall['m']    

    node_dist = stats.iloc[:-1]['n']

    total_n = node_dist.sum()
    total_m = stats.iloc[:-1]['m'].sum()

    min_cluster = node_dist.min()
    q1_cluster = node_dist.quantile(0.25)
    med_cluster = node_dist.median()
    mean_cluster = node_dist.mean()
    q3_cluster = node_dist.quantile(0.75)
    max_cluster = node_dist.max()

    modularity = overall['modularity']
    modularities = stats.iloc[:-1]['modularity']

    modularity_min = modularities.min()
    modularity_q1 = modularities.quantile(0.25)
    modularity_med = modularities.median()
    modularity_mean = modularities.mean()
    modularity_q3 = modularities.quantile(0.75)
    modularity_max = modularities.max()

    cpm_score = overall['cpm_score']
    cpm_scores = stats.iloc[:-1]['cpm_score']

    cpm_min = cpm_scores.min()
    cpm_q1 = cpm_scores.quantile(0.25)
    cpm_med = cpm_scores.median()
    cpm_mean = cpm_scores.mean()
    cpm_q3 = cpm_scores.quantile(0.75)
    cpm_max = cpm_scores.max()

    conductances = stats.iloc[:-1]['conductance']
    conductance_min = conductances.min()
    conductance_q1 = conductances.quantile(0.25)
    conductance_med = conductances.median()
    conductance_mean = conductances.mean()
    conductance_q3 = conductances.quantile(0.75)
    conductance_max = conductances.max()

    mincuts = stats.iloc[:-1]['connectivity']
    mincuts_normalized = stats.iloc[:-1]['connectivity_normalized']

    mincuts_min = mincuts.min()
    mincuts_max = mincuts.max()
    mincuts_med = mincuts.median()
    mincuts_q1 = mincuts.quantile(0.25)
    mincuts_q3 = mincuts.quantile(0.75)
    mincuts_mean = mincuts.mean()
    mincuts_normalized_min = mincuts_normalized.min()
    mincuts_normalized_max = mincuts_normalized.max()
    mincuts_normalized_med = mincuts_normalized.median()
    mincuts_normalized_q1 = mincuts_normalized.quantile(0.25)
    mincuts_normalized_q3 = mincuts_normalized.quantile(0.75)
    mincuts_normalized_mean = mincuts_normalized.mean()

    summary_stats = pd.Series({
        'network': argv[2],
        'num_clusters': stats.shape[0] - 1,
        'network_n': n,
        'network_m': m,
        'total_n': total_n,
        'total_m': total_m,
        'cluster_size_dist': [min_cluster, q1_cluster, med_cluster, q3_cluster, max_cluster],
        'mean_cluster_size': mean_cluster,
        'total_modularity': modularity,
        'modularity_dist': [modularity_min, modularity_q1, modularity_med, modularity_q3, modularity_max],
        'modularity_mean': modularity_mean,
        'total_cpm_score': cpm_score,
        'cpm_dist': [cpm_min, cpm_q1, cpm_med, cpm_q3, cpm_max],
        'cpm_mean': cpm_mean,
        'conductance_dist': [conductance_min, conductance_q1, conductance_med, conductance_q3, conductance_max],
        'conductance_mean': conductance_mean,
        'mincuts_dist': [mincuts_min, mincuts_q1, mincuts_med, mincuts_q3, mincuts_max],
        'mincuts_mean': mincuts_mean,
        'mincuts_normalized_dist': [mincuts_normalized_min, mincuts_normalized_q1, mincuts_normalized_med, mincuts_normalized_q3, mincuts_normalized_max],
        'mincuts_mean_normalized': mincuts_normalized_mean,
    })

    return summary_stats

# Read the file line by line and store in an array
lines_array = []
with open('config.tsv', 'r') as file:
    for line in file:
        lines_array.append(line.strip())

names = ['clustering,resolution,clusterer']
config_csv = '\n'.join(names + [re.sub(r'\s+', ',', line) for line in lines_array])

config = pd.read_csv(StringIO(config_csv))

clusterings = list(config['clustering'])
clustering_stats = [os.path.splitext(filename)[0] + '_stats.csv' for filename in clusterings]
summaries = [summarize_stats(clustering_stat) for clustering_stat in clustering_stats]

summary_df = pd.concat(summaries, axis=1)
summary_df.columns = clusterings
summary_df = summary_df.T

print()

summary_df.to_csv(f'{argv[1]}/summary.csv')
