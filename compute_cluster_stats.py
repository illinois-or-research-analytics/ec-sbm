import sys
import csv
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkit as nk

from utils import from_existing_clustering, viecut, Graph

network_id = sys.argv[1]
resolution = sys.argv[2]
method = sys.argv[3]
based_on = sys.argv[4]

print(
    f'Cluster statistics for {network_id} at resolution {resolution} using {method}')

_dir = f'data/networks/{method}/{based_on}/{network_id}/leiden{resolution}/'

if 'abcd' in method:
    # Compute input mcs
    mcs_fn = 'mcs.dat'
    cs_fn = 'cs.dat'

    with open(f'{_dir}/{mcs_fn}') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        mcs = [int(row[0]) for row in csv_reader]

        # Index column for dataframe
        mcs = [{'id': i + 1, 'mcs': mcs[i]} for i in range(len(mcs))]
        df = pd.DataFrame(mcs, columns=['id', 'mcs'])

    with open(f'{_dir}/{cs_fn}') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        cs = [int(row[0]) for row in csv_reader]

        # Index column for dataframe
        cs = {
            int(i + 1): cs[i]
            for i in range(len(cs))
        }
        df['size'] = df['id'].map(cs)

    # Compute generated mcs
    edge_fn = 'edge.dat'
    com_fn = 'com.dat'

    edgelist_reader = nk.graphio.EdgeListReader("\t", 0)
    nk_graph = edgelist_reader.read(f'{_dir}/{edge_fn}')
    G = Graph(nk_graph, "")

    clusters = \
        from_existing_clustering(f'{_dir}/{com_fn}')

    clusters = {
        int(k): cluster.realize(G)
        for k, cluster in clusters.items()
    }

    mincut_results = {
        k: viecut(cluster)[-1] if cluster.n() > 1 else 1
        for k, cluster in clusters.items()
    }

    size = {
        k: cluster.n()
        for k, cluster in clusters.items()
    }

    mindegs = {
        k: min([
            cluster.internal_degree(u, G)
            for u in cluster.nodeset
        ])
        for k, cluster in clusters.items()
    }

    df['mcs_gen'] = df['id'].map(mincut_results)
    df['size_gen'] = df['id'].map(size)
    df['mindeg_gen'] = df['id'].map(mindegs)

    # Save dataframe
    df.to_csv(f'{_dir}/mcs.csv', index=False)

    # Scatter plot (mcs, mcs_gen)
    plt.figure(figsize=(6, 6))
    fig, ax = plt.subplots(1, 1, figsize=(5, 5), dpi=300, tight_layout=True)

    m = min(df['mcs'].min(), df['mcs_gen'].min()) - 1
    M = max(df['mcs'].max(), df['mcs_gen'].max()) + 1
    ax.set_xlim(m, M)
    ax.set_ylim(m, M)
    ax.set_aspect('equal')
    ax.plot([0, 1], [0, 1],
            transform=ax.transAxes,
            color='red', linestyle='--')

    sns.scatterplot(ax=ax, data=df,
                    x='mcs', y='mcs_gen',
                    alpha=0.5)
    ax.set_xlabel('Input MCS')
    ax.set_ylabel('Generated MCS')

    plt.savefig(f'{_dir}/mcs_compare.png')
    plt.clf()
    plt.close()
else:
    edge = 'edge' if 'abcd' in method else 'network'
    com = 'com' if 'abcd' in method else 'community'
