import os
import networkx as nx
import matplotlib.pyplot as plt
import time
from collections import Counter
import numpy as np

import scipy
import pandas as pd
import json

network_id = 'cen'
resolution = '.001'

lfr_dir = f'data/networks/{network_id}_lfr_networks/{network_id}_leiden{resolution}_lfr'

abcd_dir = f'data/networks/{network_id}_abcd_networks/{network_id}_leiden{resolution}_abcd'
if not os.path.exists(abcd_dir):
    os.system(f'mkdir -p {abcd_dir}')


def gen_lfr(stats_path, cmin):
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
        net_cluster_stats['max-cluster-size'] = 1000

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


network_stats_json_path = f'data/network_params/{network_id}_leiden{resolution}.json'
minc = 9
N, k, mink, maxk, mu, maxc, minc, t1, t2 = gen_lfr(
    network_stats_json_path, minc)

base_path = os.getcwd()

cmd = base_path + '/package1/binary_networks/benchmark' \
    + ' -N ' + str(N) \
    + ' -k ' + str(k) \
    + ' -maxk ' + str(maxk) \
    + ' -mu ' + str(mu) \
    + ' -maxc ' + str(maxc) \
    + ' -minc ' + str(minc) \
    + ' -t1 ' + str(t1) \
    + ' -t2 ' + str(t2)

print(cmd)

lfr_net_dir = 'data/output/' + \
    os.path.basename(network_stats_json_path).replace('.json', '') + "_lfr"
if not os.path.exists(lfr_net_dir):
    os.system('mkdir -p ' + lfr_net_dir)

os.chdir(lfr_net_dir)
try:
    start = time.perf_counter()
    os.system(cmd)
    elapsed = time.perf_counter() - start
    print(f"Generation time: {elapsed}")
finally:
    os.chdir(base_path)
