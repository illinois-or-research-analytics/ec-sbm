import csv
import json
from collections import defaultdict
from typing import Dict, List

import numpy as np
import os
import networkx as nx

from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph
from hm01.mincut import viecut


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
        if n1 not in node2com or n2 not in node2com:
            continue
        if node2com[n1] == node2com[n2]:  # nodes are co-clustered
            in_degree[n1] += 1
            in_degree[n2] += 1
        else:
            out_degree[n1] += 1
            out_degree[n2] += 1
    outs = [out_degree[i] for i in G.nodes]
    xi = np.sum(outs) / 2 / len(G.edges)
    return xi


def set_up(method, based_on, network_id, resolution, use_existing_clustering=False):
    output_dir = \
        f'data/networks/{method}/{based_on}/{network_id}/leiden{resolution}'
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(f'{output_dir}/deg.dat') \
            or not os.path.exists(f'{output_dir}/cs.dat') \
            or not os.path.exists(f'{output_dir}/params.json') \
            or (use_existing_clustering and (
                not os.path.exists(f'{output_dir}/com.dat')
                or not os.path.exists(f'{output_dir}/mcs.dat')
            )):

        if based_on == 'lfr':
            lfr_dir = \
                f'data/networks/lfr/{network_id}_lfr_networks/{
                    network_id}_leiden{resolution}_lfr'

            G = nx.read_edgelist([
                ' '.join(x.strip().split('\t'))
                for x in open(f'{lfr_dir}/network.dat').readlines()
            ])

            comm_fn = f'{lfr_dir}/community.dat'
        elif based_on in ['leiden_cpm', 'leiden_cpm_cm']:
            _dir = \
                f'data/networks/orig/{based_on}/{network_id}/leiden{resolution}'

            G = nx.read_edgelist([
                ' '.join(x.strip().split('\t'))
                for x in open(f'{_dir}/edge.dat').readlines()
            ])

            comm_fn = f'{_dir}/com.dat'

        if not os.path.exists(f'{output_dir}/params.json'):
            # Find mu
            mu = None

            network_stats_json_path = \
                f'data/network_params/{network_id}_leiden{resolution}.json'
            if os.path.exists(network_stats_json_path):
                _, _, _, _, mu, _, _, _, _ = \
                    process_stats_to_params(network_stats_json_path, 0)

            # Set seed
            seed = 0

            # Generate xi
            xi = compute_xi(G, comm_fn)

            with open(f'{output_dir}/params.json', 'w') as f:
                json.dump({
                    'seed': seed,
                    'xi': xi,
                    'mu': mu
                }, f)

        if not os.path.exists(f'{output_dir}/deg.dat') \
                or not os.path.exists(f'{output_dir}/cs.dat') \
                or (use_existing_clustering and (
                    not os.path.exists(f'{output_dir}/com.dat')
                    or not os.path.exists(f'{output_dir}/mcs.dat')
                )):
            cs = {}
            node_degree = []

            if use_existing_clustering:
                node_comm = []

            for line in open(comm_fn).readlines():
                u, c = line.strip().split('\t')

                if u in G.nodes:
                    node_degree.append((u, len(G[u])))

                    cs.setdefault(c, 0)
                    cs[c] += 1

                    if use_existing_clustering:
                        node_comm.append((u, c))

            comm_size = [
                (c, cs[c])
                for c in cs
            ]

            node_degree = sorted(node_degree, reverse=True, key=lambda x: x[1])
            degree = [[x[1]] for x in node_degree]
            with open(f'{output_dir}/deg.dat', 'w') as f:
                csv_writer = csv.writer(f, delimiter='\t')
                csv_writer.writerows(degree)

            comm_size = sorted(comm_size, reverse=True, key=lambda x: x[1])
            cs = [[x[1]] for x in comm_size]
            with open(f'{output_dir}/cs.dat', 'w') as f:
                csv_writer = csv.writer(f, delimiter='\t')
                csv_writer.writerows(cs)
                f.close()

            if use_existing_clustering:
                node_relabeled = {
                    u: i
                    for i, (u, _) in enumerate(node_degree, 1)
                }

                comm_relabeled = {
                    c: i
                    for i, (c, _) in enumerate(comm_size, 1)
                }

                node_comm = [
                    [node_relabeled[u], comm_relabeled[c]]
                    for u, c in node_comm
                ]

                with open(f'{output_dir}/com.dat', 'w') as f:
                    csv_writer = csv.writer(f, delimiter='\t')
                    csv_writer.writerows(node_comm)
                    f.close()

                G = nx.relabel_nodes(G, node_relabeled)
                clusters = \
                    from_existing_clustering(f'{output_dir}/com.dat')

                mincut_results = {
                    int(k): viecut(cluster.realize(G))[-1]
                    for k, cluster in clusters.items()
                }

                mcs = [None for _ in range(len(clusters))]
                for k, m in mincut_results.items():
                    mcs[k - 1] = [m]

                with open(f'{output_dir}/mcs.dat', 'w') as f:
                    csv_writer = csv.writer(f, delimiter='\t')
                    csv_writer.writerows(mcs)
                    f.close()

    return output_dir
