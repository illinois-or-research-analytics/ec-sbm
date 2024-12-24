from pathlib import Path
import os

networks = ["bibsonomy", "dblp_coauthor_snap",
            "google", "google_web", "wordnet"]

root_network = Path('data/networks')
root_stats = Path('data/stats')

# Delete all folders root_network/method_name/sbm/network_name/resolution_name/0/
# Print first

for network in networks:
    for _dir in root_network.glob(f'*/sbm/{network}/*'):
        if 'orig' in str(_dir):
            continue

        if 'RECCS' in str(_dir):
            continue

        target1 = str(_dir.parent)
        target2 = str(_dir.parent).replace('networks', 'stats')

        os.system(f'rm -rf {target1}')
        os.system(f'rm -rf {target2}')
        # print(f'rm -rf {_dir}/0/')
