import os

src = './data/cm_plus_plus_data'
tgt1 = './data/networks/leiden_cpm'
tgt2 = './data/networks/leiden_cpm_cm'

networks = ['cen', 'cit_hepph', 'cit_patents',
            'orkut', 'wiki_talk', 'wiki_topcats']
resolutions = ['.0001', '.001', '.01', '.1', '.5']

for network in networks:
    subdir_src = f'{src}/{network}/{network}_leiden_cpm/'
    subdir_tgt1 = f'{tgt1}/{network}/'
    subdir_tgt2 = f'{tgt2}/{network}/'

    for resolution in resolutions:
        subsubdir_tgt1 = f'{subdir_tgt1}/leiden{resolution}/'
        subsubdir_tgt2 = f'{subdir_tgt2}/leiden{resolution}/'

        os.makedirs(subsubdir_tgt1, exist_ok=True)
        os.makedirs(subsubdir_tgt2, exist_ok=True)

        os.system(
            f'cp {subdir_src}/S1_{network}_cleanup.tsv {subsubdir_tgt1}/edge.dat')
        os.system(
            f'cp {subdir_src}/S1_{network}_cleanup.tsv {subsubdir_tgt2}/edge.dat')

        subsubdir_src = f'{subdir_src}/res-0{resolution}-i2/'

        os.system(
            f'cp {subsubdir_src}/S2_{network}_leiden.0{resolution}_i2_clustering.tsv {subsubdir_tgt1}/com.dat')
        os.system(
            f'cp {subsubdir_src}/S6_{network}_leiden.0{resolution}_i2_post_cm_filter.R.tsv {subsubdir_tgt2}/com.dat')
