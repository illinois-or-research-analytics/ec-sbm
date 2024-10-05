import os
import csv
import json
from collections import defaultdict
from typing import Dict, List

import numpy as np
import networkx as nx
from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph
from hm01.mincut import viecut

from .constants import *


def from_existing_clustering(filepath) -> List[IntangibleSubgraph]:
    # node_id cluster_id format
    clusters: Dict[str, IntangibleSubgraph] = {}
    with open(filepath) as f:
        for line in f:
            node_id, cluster_id = line.split()
            clusters.setdefault(
                cluster_id, IntangibleSubgraph([], cluster_id)
            ).subset.append(int(node_id))
    return {key: val for key, val in clusters.items()}


def process_stats_to_params(stats_path, cmin):
    with open(stats_path) as f:
        net_cluster_stats = json.load(f)

    if int(cmin) > net_cluster_stats['max-cluster-size']:
        return

    if net_cluster_stats['node-count'] > 5000000:
        ratio = net_cluster_stats['node-count'] / 3000000
        net_cluster_stats['node-count'] = 3000000
        net_cluster_stats['max-degree'] = int(
            net_cluster_stats['max-degree'] / ratio)
        net_cluster_stats['max-cluster-size'] = int(
            net_cluster_stats['max-cluster-size'] / ratio)
        # net_cluster_stats['max-cluster-size'] = 1000

    if net_cluster_stats['mean-degree'] < 4:
        net_cluster_stats['max-degree'] = 31

    if net_cluster_stats['max-degree'] > 1000:
        net_cluster_stats['max-degree'] = 1000

    if net_cluster_stats['max-cluster-size'] > 5000:
        net_cluster_stats['max-cluster-size'] = 5000

    if net_cluster_stats['mean-degree'] > 50:
        net_cluster_stats['max-cluster-size'] = 1000

    N = net_cluster_stats['node-count']
    k = net_cluster_stats['mean-degree']
    mink = net_cluster_stats['min-degree']
    maxk = net_cluster_stats['max-degree']
    mu = net_cluster_stats['mixing-parameter']
    maxc = net_cluster_stats['max-cluster-size']
    minc = int(cmin)
    t1 = net_cluster_stats['tau1']
    t2 = net_cluster_stats['tau2']

    return N, k, mink, maxk, mu, maxc, minc, t1, t2


def compute_xi(G, comm_fn):
    node2com = {}
    for line in open(comm_fn).readlines():
        node, comm = line.strip().split('\t')
        node2com[node] = comm

    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    for n1, n2 in G.edges:
        # TODO: what to do with outliers' connections?
        # if n1 not in node2com or n2 not in node2com:
        #     continue
        if n1 not in node2com and n2 not in node2com:
            # in_degree[n1] += 1
            # in_degree[n2] += 1
            continue
        elif n1 not in node2com or n2 not in node2com:
            out_degree[n1] += 1
            out_degree[n2] += 1
            continue

        if node2com[n1] == node2com[n2]:  # nodes are co-clustered
            in_degree[n1] += 1
            in_degree[n2] += 1
        else:
            out_degree[n1] += 1
            out_degree[n2] += 1
    outs = [out_degree[i] for i in G.nodes]
    total = [in_degree[i] + out_degree[i] for i in G.nodes]
    xi = np.sum(outs) / sum(total)
    return xi


def is_setup_done(output_dir, use_existing_clustering):
    return os.path.exists(f'{output_dir}/{DEG}') \
        and os.path.exists(f'{output_dir}/{NODE_ID}') \
        and os.path.exists(f'{output_dir}/{CS}') \
        and os.path.exists(f'{output_dir}/{PARAMS}') \
        and (
            not use_existing_clustering
            or (
                os.path.exists(f'{output_dir}/{COM_INP}')
                and os.path.exists(f'{output_dir}/{MCS}')
            )
    )


def read_graph(edgelist_fn):
    f = open(edgelist_fn, 'r')
    csv_reader = csv.reader(f, delimiter='\t')
    G = nx.read_edgelist([
        ' '.join(x)
        for x in csv_reader
    ])
    f.close()
    return G


def generate_params_file(G, clustering_fn, seed, is_count_outliers, output_dir):
    params = {'seed': seed}

    xi = compute_xi(G, clustering_fn)
    params['xi'] = xi

    if is_count_outliers:
        params['n_outliers'] = count_outliers(G, clustering_fn)

    with open(f'{output_dir}/{PARAMS}', 'w') as f:
        json.dump(
            params,
            f,
        )

    print(f'[INFO] {PARAMS} file is created.')


def count_outliers(G, clustering_fn):
    f = open(clustering_fn, 'r')
    csv_reader = csv.reader(f, delimiter='\t')
    clustered_nodes = {
        u
        for u, _ in csv_reader
    }
    f.close()
    c = 0
    for u in G.nodes:
        if u not in clustered_nodes:
            c += 1
    return c


def compute_degree_and_cs(G, clustering_fn, use_existing_clustering):
    node_degree = [
        (u, len(G[u]))
        for u in G.nodes
    ]

    cs = {}
    if use_existing_clustering:
        node_comm = []

    f = open(clustering_fn, 'r')
    csv_reader = csv.reader(f, delimiter='\t')
    for u, c in csv_reader:
        assert u in G.nodes, \
            f'[ERROR] Node {u} is not in the graph.'

        cs.setdefault(c, 0)
        cs[c] += 1

        if use_existing_clustering:
            node_comm.append((u, c))
    f.close()

    if use_existing_clustering:
        return node_degree, cs, node_comm
    else:
        return node_degree, cs


def generate_degree_sequence_file(node_degree_sorted, output_dir):
    with open(f'{output_dir}/{DEG}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows([
            [x]
            for _, x in node_degree_sorted
        ])
        f.close()

    print(f'[INFO] {DEG} file is created.')


def generate_node_id_file(node_degree_sorted, output_dir):
    with open(f'{output_dir}/{NODE_ID}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows([
            [u]
            for u, _ in node_degree_sorted
        ])
        f.close()

    print(f'[INFO] {NODE_ID} file is created.')


def generate_com_id_file(comm_size, output_dir):
    with open(f'{output_dir}/{COM_ID}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows([
            [c]
            for c, _ in comm_size
        ])
        f.close()

    print(f'[INFO] {COM_ID} file is created.')


def generate_com_inp_file(comm_size, node_comm, node_relabeled, output_dir):
    comm_relabeled = {
        c: i
        for i, (c, _) in enumerate(comm_size, 1)
    }

    node_comm = [
        [node_relabeled[u], comm_relabeled[c]]
        for u, c in node_comm
    ]

    with open(f'{output_dir}/{COM_INP}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows(node_comm)
        f.close()

    print(f'[INFO] {COM_INP} file is created.')


def generate_mcs_file(G, node_relabeled, output_dir):
    G = nx.relabel_nodes(G, node_relabeled)
    clusters = from_existing_clustering(f'{output_dir}/{COM_INP}')

    mcs = [None for _ in range(len(clusters))]
    for k, cluster in clusters.items():
        mincut_result = viecut(cluster.realize(G))[-1]
        mcs[int(k) - 1] = [mincut_result]

    with open(f'{output_dir}/{MCS}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows(mcs)
        f.close()

    print(f'[INFO] {MCS} file is created.')


def set_up(
    edgelist_fn,
    clustering_fn,
    seed,
    output_dir,
    use_existing_clustering=False,
    is_count_outliers=False,
):
    # TODO: Refactor this function, this is so bad
    if os.path.exists(output_dir):
        print('[WARNING] Output directory already exists. It will be overwritten.')
    else:
        os.makedirs(output_dir)

    if is_setup_done(output_dir, use_existing_clustering):
        return

    assert os.path.exists(edgelist_fn), \
        f'Edge list file ({edgelist_fn}) does not exist.'
    assert os.path.exists(clustering_fn), \
        f'Clustering file ({clustering_fn}) does not exist.'

    G = read_graph(edgelist_fn)

    if not os.path.exists(f'{output_dir}/{PARAMS}'):
        generate_params_file(
            G,
            clustering_fn,
            seed,
            is_count_outliers,
            output_dir,
        )

    if is_setup_done(output_dir, use_existing_clustering):
        return

    if use_existing_clustering:
        node_degree, comm_size, node_comm = \
            compute_degree_and_cs(G, clustering_fn, True)
    else:
        node_degree, comm_size = \
            compute_degree_and_cs(G, clustering_fn, False)

    node_degree_sorted = sorted(
        node_degree,
        reverse=True,
        key=lambda x: x[1],
    )
    del node_degree

    node_relabeled = {
        u: i
        for i, (u, _) in enumerate(node_degree_sorted, 1)
    }

    generate_degree_sequence_file(node_degree_sorted, output_dir)
    generate_node_id_file(node_degree_sorted, output_dir)
    del node_degree_sorted

    if is_setup_done(output_dir, use_existing_clustering):
        return

    comm_size = [
        (c, comm_size[c])
        for c in comm_size
    ]

    comm_size_sorted = sorted(
        comm_size,
        reverse=True,
        key=lambda x: x[1],
    )
    del comm_size

    with open(f'{output_dir}/{CS}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows([
            [x]
            for _, x in comm_size_sorted
        ])
        f.close()

    if is_setup_done(output_dir, use_existing_clustering):
        return

    generate_com_id_file(
        comm_size_sorted,
        output_dir,
    )
    generate_com_inp_file(
        comm_size_sorted,
        node_comm,
        node_relabeled,
        output_dir,
    )
    del comm_size_sorted
    del node_comm

    if is_setup_done(output_dir, use_existing_clustering):
        return

    generate_mcs_file(G, node_relabeled, output_dir)
    del G
    del node_relabeled

    assert is_setup_done(output_dir, use_existing_clustering)


def post_process(output_dir):
    assert os.path.exists(f'{output_dir}/{EDGE}')
    assert os.path.exists(f'{output_dir}/{COM_OUT}')

    if os.path.exists(f'{output_dir}/{NODE_ID}'):
        with open(f'{output_dir}/{NODE_ID}', 'r') as f:
            csv_reader = csv.reader(f, delimiter='\t')
            node_mapping = {
                str(i): _id
                for i, (_id, *_) in enumerate(csv_reader, 1)
            }
    else:
        node_mapping = None

    if os.path.exists(f'{output_dir}/{COM_ID}'):
        with open(f'{output_dir}/{COM_ID}', 'r') as f:
            csv_reader = csv.reader(f, delimiter='\t')
            comm_mapping = {
                str(i): _id
                for i, (_id, *_) in enumerate(csv_reader, 1)
            }
    else:
        comm_mapping = None

    with open(f'{output_dir}/{EDGE}', 'r') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        edges = []
        for u, v in csv_reader:
            if node_mapping is not None:
                assert u in node_mapping
                assert v in node_mapping
                u = node_mapping[u]
                v = node_mapping[v]
            edges.append((u, v))
        f.close()

    with open(f'{output_dir}/{EDGE}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows(edges)
        f.close()

    with open(f'{output_dir}/{COM_OUT}', 'r') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        com_out = []
        for u, c in csv_reader:
            if node_mapping is not None:
                assert u in node_mapping
                u = node_mapping[u]
            if comm_mapping is not None:
                assert c in comm_mapping
                c = comm_mapping[c]
            com_out.append((u, c))
        f.close()

    with open(f'{output_dir}/{COM_OUT}', 'w') as f:
        csv_writer = csv.writer(f, delimiter='\t')
        csv_writer.writerows(com_out)
        f.close()
