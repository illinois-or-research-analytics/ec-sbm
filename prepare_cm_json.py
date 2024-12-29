from pathlib import Path
import json

split = 'val'
ref_root = Path(
    'data/leiden_clustering/110-networks-cm-no-filtering/json_files')
input_root = Path('data/networks')
output_root = Path('data/community_detection')
networks_list = f'data/networks_{split}.txt'

method = 'sbmmcsprev1+o+eL1'
clustering = 'leiden_cpm_nofiltcm'
resolution = 'leiden.1'

network_ids = [
    line.strip() for line in open(networks_list)
]

cd_clids = [
    'leiden0.1',
    'leiden0.01',
    'leiden0.001',
    'leiden0.0001',
    'leidenmod',
    'infomap'
]

for cd_clid in cd_clids:
    for network_id in network_ids:
        if 'leiden0.' in cd_clid:
            ref_json_fp = ref_root / f'{network_id}_pipeline_leiden0.1.json'
        else:
            ref_json_fp = ref_root / f'{network_id}_pipeline_{cd_clid}.json'

        if not ref_json_fp.exists():
            print(f'{ref_json_fp} does not exist')
            if 'leiden0.' in cd_clid:
                ref_json_fp = ref_root / f'cen_pipeline_leiden0.1.json'
            else:
                ref_json_fp = ref_root / f'cen_pipeline_{cd_clid}.json'

        with open(ref_json_fp) as f:
            ref_json = json.load(f)

        if cd_clid == 'leiden0.1':
            cd_clustering = 'leiden_cpm'
            cd_resolution = 'leiden.1'
        elif cd_clid == 'leiden0.01':
            cd_clustering = 'leiden_cpm'
            cd_resolution = 'leiden.01'
        elif cd_clid == 'leiden0.001':
            cd_clustering = 'leiden_cpm'
            cd_resolution = 'leiden.001'
        elif cd_clid == 'leiden0.0001':
            cd_clustering = 'leiden_cpm'
            cd_resolution = 'leiden.0001'
        elif cd_clid == 'leidenmod':
            cd_clustering = 'leiden_mod'
            cd_resolution = 'leidenmod'
        elif cd_clid == 'infomap':
            cd_clustering = 'infomap'
            cd_resolution = 'infomap'
        else:
            raise ValueError(f'cd_clid {cd_clid} not recognized')

        out_dir = output_root / method / \
            clustering / network_id / resolution / '0' / cd_clustering / cd_resolution
        out_dir.mkdir(parents=True, exist_ok=True)

        cm_json = ref_json.copy()
        cm_json['title'] = f'{network_id}_{
            method}_{clustering}_0_{cd_resolution}'
        cm_json['name'] = network_id
        cm_json['input_file'] = str((input_root / method /
                                    clustering / network_id / resolution / '0' / 'edge.tsv').absolute())
        cm_json['output_dir'] = '.'
        cm_json['stages'] = [
            stage
            for stage in cm_json['stages']
            if stage['name'] != 'stats'
        ]

        if cd_clid == 'leiden0.1':
            cm_json['params'][0]['res'] = 0.1
        elif cd_clid == 'leiden0.01':
            cm_json['params'][0]['res'] = 0.01
        elif cd_clid == 'leiden0.001':
            cm_json['params'][0]['res'] = 0.001
        elif cd_clid == 'leiden0.0001':
            cm_json['params'][0]['res'] = 0.0001
        elif cd_clid == 'leidenmod':
            pass
        elif cd_clid == 'infomap':
            assert cm_json['stages'][-1]['name'] == 'connectivity_modifier'
            cm_json['stages'][-1]['cfile'] = '/home/vltanh/synnet/cm_pipeline/hm01/clusterers/external_clusterers/infomap_wrapper.py'
        else:
            raise ValueError(f'cd_clid {cd_clid} not recognized')

        with open(out_dir / 'pipeline.json', 'w') as f:
            json.dump(cm_json, f, indent=4)
