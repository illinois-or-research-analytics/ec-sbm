import json
from collections import defaultdict

import numpy as np
import os
import networkx as nx


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
        if node2com[n1] == node2com[n2]:  # nodes are co-clustered
            in_degree[n1] += 1
            in_degree[n2] += 1
        else:
            out_degree[n1] += 1
            out_degree[n2] += 1
    outs = [out_degree[i] for i in G.nodes]
    xi = np.sum(outs) / 2 / len(G.edges)
    return xi


def set_up(method, based_on, network_id, resolution):
    output_dir = \
        f'data/networks/{method}_{based_on}/{network_id}/leiden{resolution}'
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(f'{output_dir}/deg.dat') \
            or not os.path.exists(f'{output_dir}/cs.dat') \
            or not os.path.exists(f'{output_dir}/params.json'):

        if based_on == 'lfr':
            lfr_dir = f'data/networks/lfr/{network_id}_lfr_networks/{
                network_id}_leiden{resolution}_lfr'

            G = nx.read_edgelist([' '.join(x.strip().split('\t')) for x in open(
                f'{lfr_dir}/network.dat').readlines()])

            comm_fn = f'{lfr_dir}/community.dat'
        elif based_on == 'leiden_cpm':
            _dir = \
                f'data/networks/leiden_cpm/{network_id}/leiden{resolution}'

            G = nx.read_edgelist([
                ' '.join(x.strip().split('\t'))
                for x in open(f'{_dir}/edge.dat').readlines()
            ])

            comm_fn = f'{_dir}/com.dat'

        if not os.path.exists(f'{output_dir}/deg.dat') or not os.path.exists(f'{output_dir}/cs.dat'):
            cs = {}
            degree = []
            for line in open(comm_fn).readlines():
                u, c = line.strip().split('\t')

                if u in G.nodes:
                    degree.append(len(G[u]))

                    cs.setdefault(c, 0)
                    cs[c] += 1

            degree = sorted(degree, reverse=True)
            with open(f'{output_dir}/deg.dat', 'w') as f:
                f.write('\n'.join(map(str, degree)))

            cs = sorted(cs.values(), reverse=True)
            with open(f'{output_dir}/cs.dat', 'w') as f:
                f.write('\n'.join(map(str, cs)))

        if not os.path.exists(f'{output_dir}/params.json'):
            network_stats_json_path = f'data/network_params/{
                network_id}_leiden{resolution}.json'
            _, _, _, _, mu, _, _, _, _ = \
                process_stats_to_params(network_stats_json_path, 0)

            seed = 0

            # Generate xi
            xi = compute_xi(G, comm_fn)

            with open(f'{output_dir}/params.json', 'w') as f:
                json.dump({
                    'seed': seed,
                    'xi': xi,
                    'mu': mu
                }, f)

    return output_dir
