from pathlib import Path
import json

root = Path('data/stats')

for method_dir in root.iterdir():
    print('====================')
    method_id = method_dir.name
    for clustering_dir in method_dir.iterdir():
        print('================')
        clustering_id = clustering_dir.name
        for network_dir in clustering_dir.iterdir():
            network_id = network_dir.name

            for resolution_dir in network_dir.iterdir():
                resolution_id = resolution_dir.name

                gt_stats_fp = resolution_dir / '0' / 'gt_stats.json'

                if not gt_stats_fp.exists():
                    continue

                print(f'Processing {
                      method_id}/{clustering_id}/{network_id}/{resolution_id}')

                with gt_stats_fp.open() as f:
                    gt_stats = json.load(f)

                if 'characteristic_time' in gt_stats:
                    del gt_stats['characteristic_time']

                if 'tau' in gt_stats:
                    gt_stats['char_time'] = 1 / gt_stats['tau']

                    with gt_stats_fp.open('w') as f:
                        json.dump(gt_stats, f, indent=4)
