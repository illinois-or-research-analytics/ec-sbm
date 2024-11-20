import sys
import os
import time

import networkx as nx

from utils import process_stats_to_params

# network_id = 'cen'
# resolution = '.001'

network_id = sys.argv[1]
resolution = sys.argv[2]
method = 'abcds'

lfr_dir = f'data/networks/{network_id}_lfr_networks/{network_id}_leiden{resolution}_lfr'

abcds_dir = f'data/networks/{network_id}_{method}_networks/{network_id}_leiden{resolution}_{method}'
if not os.path.exists(abcds_dir):
    os.system(f'mkdir -p {abcds_dir}')

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

if network_id == 'cen':
    mink = 5
elif network_id == 'wiki_talk':
    mink = 1
elif network_id == 'wiki_topcats':
    mink = 9
elif network_id == 'cit_patents':
    mink = 5
elif network_id == 'cit_hepph':
    mink = 15
elif network_id == 'oc':
    mink = 18

seed = 0
xi = mu

with open(f'{abcds_dir}/config.toml', 'w') as f:
    f.write(
        f'''seed = ""                   # RNG seed, use "" for no seeding
n = "{N}"                   # number of vertices in graph
t1 = "{t1}"                      # power-law exponent for degree distribution
d_min = "{mink}"                   # minimum degree
d_max = "{maxk}"                  # maximum degree
d_max_iter = "{1000}"           # maximum number of iterations for sampling degrees
t2 = "{t2}"                      # power-law exponent for cluster size distribution
c_min = "{minc}"                  # minimum cluster size
c_max = "{maxc}"                # maximum cluster size
c_max_iter = "{1000}"           # maximum number of iterations for sampling cluster sizes
# Exactly one of xi and mu must be passed as Float64. Also if xi is provided islocal must be set to false or omitted.
xi = "{xi}"                    # fraction of edges to fall in background graph
#mu = "0.2"                   # mixing parameter
islocal = "false"             # if "true" mixing parameter is restricted to local cluster, otherwise it is global
isCL = "false"                # if "false" use configuration model, if "true" use Chung-Lu
degreefile = "{abcds_dir}/deg.dat"        # name of file do generate that contains vertex degrees
communitysizesfile = "{abcds_dir}/cs.dat" # name of file do generate that contains community sizes
communityfile = "{abcds_dir}/com.dat"     # name of file do generate that contains assignments of vertices to communities
networkfile = "{abcds_dir}/edge.dat"      # name of file do generate that contains edges of the generated graph
nout = "0"                  # number of vertices in graph that are outliers; optional parameter
                            # if nout is passed and is not zero then we require islocal = "false",
                            # isCL = "false", and xi (not mu) must be passed
                            # if nout > 0 then it is recommended that xi > 0'''
    )

print(
    f'Generating ABCDs network for {network_id} with resolution {resolution}...')

start = time.perf_counter()
os.system(
    f'julia ABCDGraphGenerator.jl/utils/abcd_sampler.jl {abcds_dir}/config.toml')
elapsed = time.perf_counter() - start

print(f"Generation time: {elapsed}")
