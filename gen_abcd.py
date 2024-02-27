import sys
import os
import time
import json
from collections import defaultdict

import networkx as nx
import numpy as np

from utils import process_stats_to_params


def compute_xi(G, comm_fn):
    node2com = {}
    for line in open(comm_fn).readlines():
        node, comm = map(int, line.strip().split('\t'))
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


network_id = sys.argv[1]
resolution = sys.argv[2]

method = 'abcd'
output_dir = f'data/networks/{method}/{network_id}_{method}_networks/{network_id}_leiden{resolution}_{method}'
os.makedirs(output_dir, exist_ok=True)

# == Read generated LFR network
if not os.path.exists(f'{output_dir}/deg.dat') \
        or not os.path.exists(f'{output_dir}/cs.dat') \
        or not os.path.exists(f'{output_dir}/params.json'):

    lfr_dir = f'data/networks/lfr/{network_id}_lfr_networks/{network_id}_leiden{resolution}_lfr'

    # Load network
    G = nx.read_edgelist([' '.join(x.strip().split('\t')) for x in open(
        f'{lfr_dir}/network.dat').readlines()], nodetype=int)

    if not os.path.exists(f'{output_dir}/deg.dat'):
        # Generate degree sequence
        degree = []
        for u in G.nodes:
            degree.append(len(G[u]))
        degree = sorted(degree, reverse=True)

        with open(f'{output_dir}/deg.dat', 'w') as f:
            f.write('\n'.join(map(str, degree)))

    if not os.path.exists(f'{output_dir}/cs.dat'):
        # Generate community size sequence
        cs = {}
        for line in open(f'{lfr_dir}/community.dat').readlines():
            node, comm = map(int, line.strip().split('\t'))
            cs.setdefault(comm, 0)
            cs[comm] += 1
        cs = sorted(cs.values(), reverse=True)

        with open(f'{output_dir}/cs.dat', 'w') as f:
            f.write('\n'.join(map(str, cs)))

    if not os.path.exists(f'{output_dir}/params.json'):
        network_stats_json_path = f'data/network_params/{network_id}_leiden{resolution}.json'
        _, _, _, _, mu, _, _, _, _ = \
            process_stats_to_params(network_stats_json_path, 0)

        seed = 0

        # Generate xi
        xi = compute_xi(G, f'{lfr_dir}/community.dat')

        with open(f'{output_dir}/params.json', 'w') as f:
            json.dump({
                'seed': seed,
                'xi': xi,
                'mu': mu
            }, f)

with open(f'{output_dir}/params.json', 'r') as f:
    params = json.load(f)
    seed = params['seed']
    xi = params['xi']
    mu = params['mu']

# == Generate ABCD network
print(
    f'Generating ABCD network for {network_id} with resolution {resolution}...')
print(f'Mixing parameter (mu) {mu}')
print(f'Mixing parameter (xi) {xi}')

cmd = f'julia ABCDGraphGenerator.jl/utils/graph_sampler.jl \
                {output_dir}/edge.dat {output_dir}/com.dat \
                {output_dir}/deg.dat {output_dir}/cs.dat \
                xi {xi} false false {seed} 0'

with open(f'{output_dir}/run.log', 'w') as f:
    f.write(cmd)
    f.write('\n')

    start = time.perf_counter()
    os.system(cmd)
    elapsed = time.perf_counter() - start

    f.write(f"Generation time: {elapsed}")
