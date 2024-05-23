import os
import csv
import argparse

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkit as nk

from src.utils import from_existing_clustering, viecut, Graph
from src.constants import *


def with_bijection(_dir):
    # Compute input mcs
    mcs_fn = MCS
    cs_fn = CS

    comm_mapping = {}
    with open(f'{_dir}/{COM_ID}') as f:
        reader = csv.reader(f, delimiter='\t')
        for i, (comm_id, *_) in enumerate(reader, 1):
            comm_mapping[i] = comm_id

    with open(f'{_dir}/{mcs_fn}') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        mcs = [int(row[0]) for row in csv_reader]

        # Index column for dataframe
        mcs = [
            {
                'id': comm_mapping[i + 1],
                'mcs': mcs[i],
            }
            for i in range(len(mcs))
        ]
        df = pd.DataFrame(mcs, columns=['id', 'mcs'])

    with open(f'{_dir}/{cs_fn}') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        cs = [int(row[0]) for row in csv_reader]

        # Index column for dataframe
        cs = {
            comm_mapping[i + 1]: cs[i]
            for i in range(len(cs))
        }
        df['size'] = df['id'].map(cs)

    # Compute generated mcs
    edge_fn = EDGE
    com_fn = COM_OUT

    edgelist_reader = nk.graphio.EdgeListReader(
        "\t",
        0,
        # continuous=False,
        directed=False,
    )
    nk_graph = edgelist_reader.read(f'{_dir}/{edge_fn}')
    G = Graph(nk_graph, None)

    clusters = \
        from_existing_clustering(f'{_dir}/{com_fn}')

    clusters = {
        k: cluster.realize(G)
        for k, cluster in clusters.items()
    }

    mincut_results = {
        k: viecut(cluster)[-1]
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


def without_bijection(_dir):
    # Compute input mcs
    with open(f'{_dir}/{MCS}') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        mcs = [int(row[0]) for row in csv_reader]

    df = pd.DataFrame(mcs, columns=['mcs'])
    df = df.groupby('mcs').size().reset_index(name='count')

    # Compute generated mcs
    elr = nk.graphio.EdgeListReader(
        separator="\t",
        firstNode=0,
        # continuous=False,
        directed=False,
    )
    G = Graph(elr.read(f'{_dir}/{EDGE}'), None)
    clusters = from_existing_clustering(f'{_dir}/{COM_OUT}')
    clusters = [cluster.realize(G) for cluster in clusters.values()]
    mcs_gen = [viecut(cluster)[-1] for cluster in clusters]

    df_gen = pd.DataFrame(mcs_gen, columns=['mcs'])
    df_gen.to_csv(f'{_dir}/mcs_gen.tsv', index=False, sep='\t', header=False)
    df_gen = df_gen.groupby('mcs').size().reset_index(name='count')

    # Plot the mcs distributions
    _, ax = plt.subplots(1, 1, figsize=(5, 5), dpi=300, tight_layout=True)
    sns.scatterplot(ax=ax, data=df, x='mcs',
                    y='count', label='Input', alpha=0.5)
    sns.scatterplot(ax=ax, data=df_gen, x='mcs',
                    y='count', label='Generated', alpha=0.5)
    ax.set_xlabel('Minimum cut size')
    ax.set_ylabel('Count (log)')
    ax.legend()
    # ax.set_xscale('log')
    ax.set_yscale('log')
    plt.savefig(f'{_dir}/mcs_dist.png')
    plt.clf()
    plt.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--network-id', type=str, required=True)
    parser.add_argument('--resolution', type=str, required=True)
    parser.add_argument('--method', type=str, required=True)
    parser.add_argument('--based_on', type=str, required=True)
    parser.add_argument('--seed', type=int, required=False, default=0)
    return parser.parse_args()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--network-folder', type=str, required=True)
    parser.add_argument('--output-folder', type=str, required=True)
    parser.add_argument('--is-with-bijection', action='store_true')
    return parser.parse_args()


print('Evaluation')
print('== Input == ')

args = parse_args()
network_dir = args.network_folder
output_dir = args.output_folder

print(f'Network/Clustering: {network_dir}')
print(f'Output: {output_dir}')

print('== Output == ')

assert os.path.exists(network_dir)
os.makedirs(output_dir, exist_ok=True)

if args.is_with_bijection:
    with_bijection(network_dir)
without_bijection(network_dir)
