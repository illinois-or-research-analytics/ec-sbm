import matplotlib.pyplot as plt
from pathlib import Path
import argparse

import pandas as pd
import seaborn as sns

parser = argparse.ArgumentParser(description='Plot CD accuracy results.')
parser.add_argument('--method', type=str,
                    default='sbmmcsprev1+o+eL1', help='Method name')
parser.add_argument('--gt_clustering', type=str,
                    default='sbm_wcc', help='Ground truth clustering')
parser.add_argument('--gt_resolution', type=str,
                    default='sbm', help='Ground truth resolution')
args = parser.parse_args()

method = args.method
gt_clustering = args.gt_clustering
gt_resolution = args.gt_resolution

splits = [
    # 'val_large',
    'val_medium',
    'val_small',
]

cd_clusterings_resolutions = [
    # ('leiden_cpm', 'leiden.1'),
    ('leiden_cpm_nofiltcm', 'leiden.1'),
    # ('leiden_cpm', 'leiden.01'),
    ('leiden_cpm_nofiltcm', 'leiden.01'),
    # ('leiden_cpm', 'leiden.001'),
    ('leiden_cpm_nofiltcm', 'leiden.001'),
    # ('leiden_cpm', 'leiden.0001'),
    ('leiden_cpm_nofiltcm', 'leiden.0001'),
    # ('leiden_mod', 'leidenmod'),
    ('leiden_mod_nofiltcm', 'leidenmod'),
    # ('infomap', 'infomap'),
    ('infomap_nofiltcm', 'infomap'),
    # ('sbm', 'sbm'),
    # ('sbm_cc', 'sbm'),
    ('sbm_wcc', 'sbm'),
]

names = [
    # 'Leiden-CPM(0.1)',
    'Leiden-CPM(0.1)+CM',
    # 'Leiden-CPM(0.01)',
    'Leiden-CPM(0.01)+CM',
    # 'Leiden-CPM(0.001)',
    'Leiden-CPM(0.001)+CM',
    # 'Leiden-CPM(0.0001)',
    'Leiden-CPM(0.0001)+CM',
    # 'Leiden-Mod',
    'Leiden-Mod+CM',
    # 'InfoMap',
    'InfoMap+CM',
    # 'SBM',
    # 'SBM-CC',
    'SBM-WCC',
]


def load_cd_acc_data(root, split, method, gt_clustering, gt_resolution, cd_clusterings_resolutions, networks_list):
    network_ids = [line.strip() for line in open(networks_list)]
    cd_acc = []

    def process_accuracy_file(acc_fp, network_id, cd_clustering, cd_resolution, gt_clustering, gt_resolution, cd_clusterings_resolutions):
        if not acc_fp.exists():
            print(f'{acc_fp} does not exist')
            return None

        try:
            with open(acc_fp) as f:
                lines = list(f.readlines())
                node_coverage = float(lines[1].split(':')[1].strip())
                nmi = float(lines[2].split(':')[1].strip())
                ari = float(lines[3].split(':')[1].strip())
        except Exception as e:
            print(f'Error processing {acc_fp}: {e}')
            return None

        return {
            'network_id': network_id,
            'order': cd_clusterings_resolutions.index((cd_clustering, cd_resolution)),
            'gt_clustering': gt_clustering,
            'gt_resolution': gt_resolution,
            'cd_clustering': cd_clustering,
            'cd_resolution': cd_resolution,
            'node_coverage': node_coverage,
            'nmi': nmi,
            'ari': ari,
        }

    for network_id in network_ids:
        for cd_clustering, cd_resolution in cd_clusterings_resolutions:
            subroot = f"cd_acc_{'val' if 'val' in split else split}{
                '_sbm' if 'sbm' in cd_clustering else ''}"
            acc_fp = root / subroot / method / gt_clustering / network_id / gt_resolution / \
                '0' / cd_clustering / cd_resolution / 'accuracy.txt'
            result = process_accuracy_file(
                acc_fp, network_id, cd_clustering, cd_resolution, gt_clustering, gt_resolution, cd_clusterings_resolutions)
            if result:
                cd_acc.append(result)

    cd_acc_df = pd.DataFrame(cd_acc)
    return cd_acc_df


for split in splits:
    root = Path(f'data/comdet_acc/')
    networks_list = f'data/networks_{split}.txt'

    output_root = Path(
        f'output/comdet_acc/{split}/{method}/{gt_clustering}/{gt_resolution}/all')
    output_root.mkdir(parents=True, exist_ok=True)

    output_prefix = f'treated'

    cd_acc_df = load_cd_acc_data(
        root,
        split,
        method,
        gt_clustering,
        gt_resolution,
        cd_clusterings_resolutions,
        networks_list,
    )

    # Make box plots of NMIs with both CM and non-CM
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), dpi=150)

    sns.boxplot(
        x='order',
        y='nmi',
        data=cd_acc_df,
        notch=True,
        bootstrap=10000,
        ax=axes[0],
    )
    axes[0].set_xticks([])
    axes[0].set_xlabel('')
    axes[0].set_ylabel('NMI')
    # axes[0].set_ylim(-0.1, 1.1)
    # axes[0].legend_.remove()

    sns.boxplot(
        x='order',
        y='ari',
        data=cd_acc_df,
        notch=True,
        bootstrap=10000,
        ax=axes[1],
    )
    axes[1].set_xticks([])
    axes[1].set_xlabel('')
    axes[1].set_ylabel('ARI')
    # axes[1].set_ylim(-0.1, 1.1)
    # axes[1].legend_.remove()

    sns.boxplot(
        x='order',
        y='node_coverage',
        data=cd_acc_df,
        notch=True,
        bootstrap=10000,
        ax=axes[2],
    )
    axes[2].set_xticks(
        range(len(cd_clusterings_resolutions)),
        names,
        rotation=90,
    )
    axes[2].set_xlabel('')
    axes[2].set_ylabel('Node Coverage')
    # axes[2].set_ylim(-0.1, 1.1)
    # axes[2].legend_.remove()

    # handles, labels = axes.flatten()[0].get_legend_handles_labels()
    # fig.legend(
    #     handles,
    #     labels,
    #     loc='upper center',
    #     ncols=2,
    #     bbox_to_anchor=(0.5, 1.05),
    #     fancybox=True,
    # )
    fig.tight_layout()
    fig.savefig(
        output_root / f'{output_prefix}_boxplot.pdf', bbox_inches='tight')

    cd_acc_df.to_csv(output_root / f'{output_prefix}_table.csv', index=False)
