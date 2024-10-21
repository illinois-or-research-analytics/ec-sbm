import os
import pathlib

NETWORK_IDS = [
    'cit_hepph',
    'cit_patents',
    'wiki_talk',
    'wiki_topcats',
    'orkut',
    'cen',
]
RS = [
    # '.5',
    # '.1',
    # '.01',
    # '.001',
    # '.0001',
    # '10',
    'mod',
]

root = 'data/leiden_clustering/'
output_root = 'data/networks/orig/'

os.makedirs(output_root, exist_ok=True)

edgelist_files = dict()

S1_files = pathlib.Path(root).rglob('S1_*.tsv')
for file in S1_files:
    fn = file.stem
    network_id = fn.split('-')[0].replace('S1_', '')

    if network_id not in NETWORK_IDS:
        continue

    print('S1', network_id)
    # output_folder = f'{output_root}/{network_id}/'
    # os.makedirs(output_folder, exist_ok=True)
    # os.system(f'cp {file} {output_folder}/edge.tsv')

    edgelist_files[network_id] = file

S2_files = pathlib.Path(root).rglob('S2_*.tsv')
for file in S2_files:
    fn = file.stem

    network_id = fn.split('-')[0].replace('S2_', '')

    if network_id not in NETWORK_IDS:
        continue

    r = fn.split('-')[1].split('_')[0]

    if r[0] == '0':
        r = r[1:]

    if r not in RS:
        continue

    print('S2', network_id, r)
    output_folder = f'{output_root}/leiden_mod/{network_id}/leiden{r}/'
    os.makedirs(output_folder, exist_ok=True)
    os.system(f'cp {edgelist_files[network_id]} {output_folder}/edge.dat')
    os.system(f'cp {file} {output_folder}/com.dat')

# S5_files = pathlib.Path(root).rglob('S5_*.tsv')
# for file in S5_files:
#     fn = file.stem

#     network_id = fn.split('-')[0].replace('S5_', '').replace('_ikc.connectivity_modifier_k10', '')

#     if network_id not in NETWORK_IDS:
#         continue

#     r = fn.split('-')[1].split('_')[0]
#     if r not in RS:
#         continue

#     print('S5', network_id, r)

#     output_folder = f'{output_root}/leiden_mod_cm/{network_id}/leiden{r}/'
#     os.makedirs(output_folder, exist_ok=True)
#     os.system(f'cp {edgelist_files[network_id]} {output_folder}/edge.dat')
#     os.system(f'cp {file} {output_folder}/com.dat')

#     # os.system(
#     #     f'Rscript cm_pipeline/scripts/post_cm_filter.R {file} {output_folder}/com.tsv')

# Check result
for network_id in NETWORK_IDS:
    for r in RS:
        # if not os.path.exists(f'{output_root}/ikc_cm/{network_id}/leiden{r}/edge.dat'):
        #     print(f'{network_id} {r} S1/S2 not found')

        # if not os.path.exists(f'{output_root}/leiden_cpm/{network_id}/leiden{r}/com.dat'):
        #     print(f'{network_id} {r} S2 not found')

        if not os.path.exists(f'{output_root}/leiden_mod/{network_id}/leiden{r}/edge.dat'):
            print(f'{network_id} {r} S1 not found')

        if not os.path.exists(f'{output_root}/leiden_mod/{network_id}/leiden{r}/com.dat'):
            print(f'{network_id} {r} S2 not found')
