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
    '.5',
    '.1',
    '.01',
    '.001',
    '.0001',
]

root = '/projects/engrit/chackoge/cm_plus_plus_data/'
output_root = '/projects/engrit/chackoge/vltanh/data/networks/orig/'

os.makedirs(output_root, exist_ok=True)

ignore = len(pathlib.Path(root).parts)

S1_files = pathlib.Path(root).rglob('S1_*.tsv')
for file in S1_files:
    parts = file.parts[ignore:]

    if len(parts) != 3:
        continue
    network_id, *_ = parts

    if network_id not in NETWORK_IDS:
        continue

    print('S1', network_id)
    output_folder = f'{output_root}/{network_id}/'
    os.makedirs(output_folder, exist_ok=True)
    os.system(f'cp {file} {output_folder}/edge.tsv')

S2_files = pathlib.Path(root).rglob('S2_*.tsv')
for file in S2_files:
    parts = file.parts[ignore:]
    if len(parts) != 4:
        continue
    network_id, _, r, _ = file.parts[ignore:]

    if network_id not in NETWORK_IDS:
        continue

    _, r, _ = r.split('-')
    r = r[1:]

    if r not in RS:
        continue

    print('S2', network_id, r)
    output_folder = f'{output_root}/{network_id}/leiden_cpm/leiden{r}/'
    os.makedirs(output_folder, exist_ok=True)
    os.system(f'cp {file} {output_folder}/com.tsv')

S5_files = pathlib.Path(root).rglob('S5_*.tsv')
for file in S5_files:
    parts = file.parts[ignore:]
    if len(parts) != 4:
        continue
    network_id, _, r, _ = file.parts[ignore:]

    if network_id not in NETWORK_IDS:
        continue

    _, r, _ = r.split('-')
    r = r[1:]

    if r not in RS:
        continue

    print('S5', network_id, r)
    output_folder = f'{output_root}/{network_id}/leiden_cpm_cm/leiden{r}/'
    os.makedirs(output_folder, exist_ok=True)
    os.system(
        f'Rscript cm_pipeline/scripts/post_cm_filter.R {file} {output_folder}/com.tsv')
