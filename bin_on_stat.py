from pathlib import Path
import json
import argparse

import pandas as pd

STATS = [
    ('node_coverage', 'Node coverage'),
    ('mixing_xi', 'Global mixing parameter'),
    # ('largest_cluster_size', 'Largest cluster size'),
    # ('frac_largest_cluster', 'Fraction of nodes in largest cluster'),
    ('mean_csize', 'Mean cluster size'),
    # ('median_csize', 'Median cluster size'),
    ('n_clusters', 'Number of clusters'),
    # ('density', 'Density'),
    # ('largest_cluster_density', 'Density of largest cluster'),
    ('mean_cluster_density', 'Mean cluster density'),
    # ('deg_assort', 'Degree assortativity'),
    # ('local_ccoeff', 'Local clustering coefficient'),
    # ('global_ccoeff', 'Global clustering coefficient'),
    # ('pseudo_diameter', 'Pseudo diameter'),
    # ('node_percolation_targeted', 'Node percolation targeted'),
    # ('node_percolation_random', 'Node percolation random'),
    # ('frac_giant_ccomp', 'Fraction of nodes in giant connected component'),
    # ('char_time', 'Characteristic time'),
    # ('n_edges', 'Number of edges'),
    # ('mean_degree', 'Mean degree'),
    # ('mean_kcore', 'Mean k-core'),
]

CLUSTERING_RESOLUTION = [
    # ('ikc_cc', 'k10'),
    # ('ikc_nofiltcm', 'k10'),
    # ('infomap_cc', 'infomap'),
    # ('infomap_nofiltcm', 'infomap'),
    # ('leiden_cpm', 'leiden.1'),
    # ('leiden_cpm', 'leiden.01'),
    # ('leiden_cpm', 'leiden.001'),
    # ('leiden_mod', 'leidenmod'),
    # ('leiden_cpm_nofiltcm', 'leiden.1'),
    # ('leiden_cpm_nofiltcm', 'leiden.01'),
    # ('leiden_cpm_nofiltcm', 'leiden.001'),
    ('leiden_mod_nofiltcm', 'leidenmod'),
    # ('sbm', 'sbm'),
    # ('sbm_cc', 'sbm'),
    ('sbm_wcc', 'sbm'),
]


def get_stat_value(stat, stat_data, gt_stat_data, network_dir):
    def get_cluster_sizes(file_path):
        if not file_path.exists():
            print(f'Not found {file_path}')
            return []
        with open(file_path) as f:
            return [int(line) for line in f.readlines()]

    def get_cluster_edges(file_path):
        if not file_path.exists():
            print(f'Not found {file_path}')
            return []
        with open(file_path) as f:
            return [int(line) for line in f.readlines()]

    if stat == 'node_coverage':
        return 1 - stat_data['n_onodes'] / stat_data['n_nodes']
    elif stat == 'largest_cluster_size':
        cluster_sizes = get_cluster_sizes(
            network_dir / 'c_size.distribution')
        return max(cluster_sizes, default=0)
    elif stat == 'frac_largest_cluster':
        cluster_sizes = get_cluster_sizes(
            network_dir / 'c_size.distribution')
        return max(cluster_sizes, default=0) / stat_data['n_nodes']
    elif stat == 'mean_csize':
        cluster_sizes = get_cluster_sizes(
            network_dir / 'c_size.distribution')
        return (sum(cluster_sizes) / len(cluster_sizes) if cluster_sizes else 0) / stat_data['n_nodes']
    elif stat == 'median_csize':
        cluster_sizes = get_cluster_sizes(
            network_dir / 'c_size.distribution')
        cluster_sizes.sort()
        return (cluster_sizes[len(cluster_sizes) // 2] if cluster_sizes else 0) / stat_data['n_nodes']
    elif stat == 'n_clusters':
        return stat_data['n_clusters'] / stat_data['n_nodes']
    elif stat == 'density':
        n_nodes = stat_data['n_nodes']
        n_edges = stat_data['n_edges']
        return 2 * n_edges / (n_nodes * (n_nodes - 1))
    elif stat == 'largest_cluster_density':
        cluster_sizes = get_cluster_sizes(
            network_dir / 'c_size.distribution')
        cluster_edges = get_cluster_edges(
            network_dir / 'c_edges.distribution')
        densities = [2 * cluster_edges[i] / (cluster_sizes[i] * (
            cluster_sizes[i] - 1)) for i in range(len(cluster_sizes))]
        return max(densities, default=0)
    elif stat == 'mean_cluster_density':
        cluster_sizes = get_cluster_sizes(
            network_dir / 'c_size.distribution')
        cluster_edges = get_cluster_edges(
            network_dir / 'c_edges.distribution')
        densities = [2 * cluster_edges[i] / (cluster_sizes[i] * (
            cluster_sizes[i] - 1)) for i in range(len(cluster_sizes))]
        return sum(densities) / len(densities) if densities else 0
    elif stat in gt_stat_data:
        return gt_stat_data[stat]
    elif stat in stat_data:
        return stat_data[stat]
    else:
        raise ValueError(f'Unknown stat {stat}')


parser = argparse.ArgumentParser(
    description='Plot node coverage for networks.')
parser.add_argument('--root', type=str, required=True,
                    help='Root directory for data')
parser.add_argument('--networks_list', type=str,
                    default='data/networks_val.txt', help='File with list of network IDs')
parser.add_argument('--output', type=str, required=True,
                    help='Output folder')
args = parser.parse_args()

root = Path(args.root)
networks_list = args.networks_list
output_root = Path(args.output)

network_ids = [
    line.strip() for line in open(networks_list)
]

output_root.mkdir(parents=True, exist_ok=True)

for stat, stat_name in STATS:
    for clustering, resolution in CLUSTERING_RESOLUTION:
        stat_values = []
        for network_id in network_ids:
            network_dir = root / clustering / network_id / resolution / '0'
            if not network_dir.exists():
                print(f'No directory for {network_id} with clustering {
                    clustering} and resolution {resolution}')
                continue

            stat_file = network_dir / 'stats.json'
            if not stat_file.exists():
                print(f'Not found {stat_file}')
                continue

            gt_stat_file = network_dir / 'gt_stats.json'
            if not gt_stat_file.exists():
                print(f'Not found {gt_stat_file}')
                continue

            stat_data = json.load(stat_file.open())
            gt_stat_data = json.load(gt_stat_file.open())

            stat_value = get_stat_value(
                stat, stat_data, gt_stat_data, network_dir)
            stat_values.append(
                (network_id, stat_value)
            )

        df = pd.DataFrame(
            stat_values,
            columns=[
                'network_id',
                stat,
            ],
        )
        df.sort_values(stat, inplace=True)

        output_dir = output_root / f'{clustering}_{resolution}'
        output_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_dir / f'{stat}.csv', index=False)

        # bins = [0] + [0.1 * i for i in range(1, 10)] + [1]
        # df['bin'] = pd.cut(df[stat], bins, right=False)
        df['bin'] = pd.qcut(df[stat], 4, duplicates='drop')

        for bin_name, bin_df in df.groupby('bin', observed=True, sort=True):
            bin_output_dir = output_dir / 'bin' / stat
            bin_output_dir.mkdir(parents=True, exist_ok=True)

            bin_df[['network_id']].to_csv(
                bin_output_dir / f'{bin_name}.txt', index=False, header=False)
