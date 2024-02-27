import sys
import os
import time
from collections import defaultdict

import networkx as nx
import numpy as np

from utils import process_stats_to_params

# network_id = 'cen'
# resolution = '.001'

network_id = sys.argv[1]
resolution = sys.argv[2]

lfr_dir = f'data/networks/{network_id}_lfr_networks/{network_id}_leiden{resolution}_lfr'

abcd_dir = f'data/networks/{network_id}_abcd_networks/{network_id}_leiden{resolution}_abcd'
if not os.path.exists(abcd_dir):
    os.system(f'mkdir -p {abcd_dir}')

network_stats_json_path = f'data/network_params/{network_id}_leiden{resolution}.json'

if network_id == 'cen':
    if resolution == '.001':
        minc = 9
    elif resolution == '.01':
        minc = 10
    elif resolution == '.1':
        minc = 8
elif network_id == 'wiki_talk':
    if resolution == '.001':
        minc = 9
    elif resolution == '.01':
        minc = 19
    elif resolution == '.1':
        minc = 52
elif network_id == 'wiki_topcats':
    minc = 10
elif network_id == 'cit_patents':
    if resolution == '.001':
        minc = 14
    elif resolution == '.01':
        minc = 5
    elif resolution == '.1':
        minc = 8
elif network_id == 'cit_hepph':
    minc = 1
elif network_id == 'oc':
    if resolution == '.001':
        minc = 22
    elif resolution == '.01':
        minc = 9
    elif resolution == '.1':
        minc = 39

N, k, mink, maxk, mu, maxc, minc, t1, t2 = \
    process_stats_to_params(network_stats_json_path, minc)

# Read generated LFR network
G = nx.read_edgelist([' '.join(x.strip().split('\t')) for x in open(
    f'{lfr_dir}/network.dat').readlines()], nodetype=int)

# Generate degree sequence
degree = []
for u in G.nodes:
    degree.append(len(G[u]))
degree = sorted(degree, reverse=True)

with open(f'{abcd_dir}/deg.dat', 'w') as f:
    f.write('\n'.join(map(str, degree)))

# Generate community size sequence
cs = {}
for line in open(f'{lfr_dir}/community.dat').readlines():
    node, comm = map(int, line.strip().split('\t'))
    cs.setdefault(comm, 0)
    cs[comm] += 1
cs = sorted(cs.values(), reverse=True)

with open(f'{abcd_dir}/cs.dat', 'w') as f:
    f.write('\n'.join(map(str, cs)))

# Generate xi
node2com = {}
for line in open(f'{lfr_dir}/community.dat').readlines():
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
# edges = [out_degree[i] + in_degree[i] for i in G.nodes]
xi = np.sum(outs) / 2 / len(G.edges)

seed = 0
# xi = mu

print(
    f'Generating ABCD network for {network_id} with resolution {resolution}...')
print(f'Mixing parameter (mu) {mu}')
print(f'Mixing parameter (xi) {xi}')

cmd = f'julia ABCDGraphGenerator.jl/utils/graph_sampler.jl \
                {abcd_dir}/edge.dat {abcd_dir}/com.dat \
                {abcd_dir}/deg.dat {abcd_dir}/cs.dat \
                xi {xi} false false {seed} 0'

with open(f'{abcd_dir}/run.log', 'w') as f:
    f.write(cmd)
    f.write('\n')

    start = time.perf_counter()
    os.system(cmd)
    elapsed = time.perf_counter() - start

    f.write(f"Generation time: {elapsed}")
