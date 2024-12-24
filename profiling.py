from pathlib import Path
import re

import pandas as pd

root = Path('data/networks/')
networks_list = 'data/networks_val.txt'

network_ids = [
    line.strip() for line in open(networks_list)
]

method = 'sbmmcsprev1'
clustering = 'sbm_wcc'
resolution = 'sbm'

out_fp = Path(f'output/profiles/time_{method}_{clustering}_{resolution}.csv')
out_fp.parent.mkdir(parents=True, exist_ok=True)

all_profiles = []
for network_id in network_ids:
    profile = {
        'network_id': network_id,
    }

    # Generation of the synthetic clustered subnetwork

    syn_log_fp = root / method / clustering / \
        network_id / resolution / '0' / 'run.log'

    if not syn_log_fp.exists():
        print(f'{syn_log_fp} does not exist')
        continue

    with open(syn_log_fp, 'r') as f:
        lines = list(f.readlines())

    profile_mapping = {
        'c_setup': 'INFO - Setup: ',
        'c_gen_kec': 'INFO - Generation of k-edge-connected graphs: ',
        'c_compute_sbm': 'INFO - Computing the input to SBM-NG: ',
        'c_gen_remaining': 'INFO - Generation of the remaining network: ',
        'c_post': 'INFO - Post-processing: ',
    }

    for line in lines:
        for key, value in profile_mapping.items():
            if value in line:
                profile[key] = float(line.split(value)[1].strip())

    # Generation of the synthetic outlier subnetwork

    syn_log_fp = root / (method + '+o') / clustering / \
        network_id / resolution / '0' / 'outlier_run.log'

    if not syn_log_fp.exists():
        print(f'{syn_log_fp} does not exist')
        continue

    with open(syn_log_fp, 'r') as f:
        lines = list(f.readlines())

    profile_mapping = {
        'o_setup': 'INFO - Setup: ',
        'o_gen': 'INFO - Generation of outlier subgraph: ',
        'o_post': 'INFO - Post-process: ',
    }

    for line in lines:
        for key, value in profile_mapping.items():
            if value in line:
                profile[key] = float(line.split(value)[1].strip())

    # Combining the synthetic clustered and outlier subnetworks

    syn_log_fp = root / (method + '+o') / clustering / \
        network_id / resolution / '0' / 'combine_run.log'

    if not syn_log_fp.exists():
        print(f'{syn_log_fp} does not exist')
        continue

    with open(syn_log_fp, 'r') as f:
        lines = list(f.readlines())

    profile_mapping = {
        'o_repl_cluster': 'INFO - Replicate clustering: ',
        'o_combine': 'INFO - Combine clustered and outlier subgraphs: ',
    }

    for line in lines:
        for key, value in profile_mapping.items():
            if value in line:
                profile[key] = float(line.split(value)[1].strip())

    # Edge matching

    syn_log_fp = root / (method + '+o+eL1') / clustering / \
        network_id / resolution / '0' / 'fix_edge.log'

    if not syn_log_fp.exists():
        print(f'{syn_log_fp} does not exist')
        continue

    with open(syn_log_fp, 'r') as f:
        lines = list(f.readlines())

    profile_mapping = {
        'e_process_cluster': 'INFO - Process original clustering: ',
        'e_process_edgelist': 'INFO - Process original edgelist: ',
        'e_create_outlier_cluster': 'INFO - Create outlier clusters: ',
        'e_compute_sbm_original': 'INFO - Compute SBM parameters from original: ',
        'e_update_sbm_existing': 'INFO - Update SBM parameters with existing: ',
        'e_add_edge': 'INFO - Processed .+ nodes, adding .+ edges: ',
        'e_post_process': 'INFO - Post-process: ',
    }

    for line in lines:
        for key, value in profile_mapping.items():
            # Regex to match the line
            query = f'(.*){value}(.*)'
            result = re.search(query, line)
            if result:
                profile[key] = float(result.group(2).strip())

    # Combine edge matching

    syn_log_fp = root / (method + '+o+eL1') / clustering / \
        network_id / resolution / '0' / 'combine_run.log'

    if not syn_log_fp.exists():
        print(f'{syn_log_fp} does not exist')
        continue

    with open(syn_log_fp, 'r') as f:
        lines = list(f.readlines())

    profile_mapping = {
        'o_repl_cluster': 'INFO - Replicate clustering: ',
        'o_combine': 'INFO - Combine clustered and outlier subgraphs: ',
    }

    all_profiles.append(profile)

df = pd.DataFrame(all_profiles)
df['c_total'] = df['c_setup'] + df['c_gen_kec'] + \
    df['c_compute_sbm'] + df['c_gen_remaining'] + df['c_post']
df['o_total'] = df['o_setup'] + df['o_gen'] + df['o_post']
df['o_combine_total'] = df['o_repl_cluster'] + df['o_combine']
df['e_total'] = df['e_process_cluster'] + df['e_process_edgelist'] + df['e_create_outlier_cluster'] + \
    df['e_compute_sbm_original'] + \
    df['e_update_sbm_existing'] + df['e_add_edge'] + df['e_post_process']
df['e_combine_total'] = df['o_repl_cluster'] + df['o_combine']
df['total'] = df['c_total'] + df['o_total'] + \
    df['o_combine_total'] + df['e_total'] + df['e_combine_total']
df.sort_values('total', inplace=True, ascending=False)
df.to_csv(str(out_fp), index=False)
