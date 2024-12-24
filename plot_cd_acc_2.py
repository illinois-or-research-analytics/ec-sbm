import matplotlib.pyplot as plt
from pathlib import Path

import pandas as pd
import seaborn as sns

root = Path('output/cd_acc_nmi_ari')

method = 'sbmmcsprev1+o+eL1'
gt_clustering = 'sbm_wcc'
gt_resolution = 'sbm'

cd_clusterings_resolutions = [
    ('leiden_cpm', 'leiden.1'),
    ('leiden_cpm', 'leiden.01'),
    ('leiden_cpm', 'leiden.001'),
    ('leiden_cpm', 'leiden.0001'),
    ('leiden_mod', 'leidenmod'),
    ('infomap', 'infomap'),
]

names = [
    'Leiden-CPM(0.1)',
    'Leiden-CPM(0.01)',
    'Leiden-CPM(0.001)',
    'Leiden-CPM(0.0001)',
    'Leiden-Mod',
    'InfoMap',
]


def load_cd_acc_data(root, method, gt_clustering, gt_resolution, cd_clusterings_resolutions, networks_list):
    network_ids = [line.strip() for line in open(networks_list)]
    cd_acc = []

    for network_id in network_ids:
        for cd_clustering, cd_resolution in cd_clusterings_resolutions:
            acc_fp = root / method / gt_clustering / network_id / gt_resolution / \
                '0' / cd_clustering / cd_resolution / 'accuracy.txt'
            if not acc_fp.exists():
                print(f'{acc_fp} does not exist')
                continue

            with open(acc_fp) as f:
                lines = list(f.readlines())
                node_coverage = float(lines[1].split(':')[1].strip())
                nmi = float(lines[2].split(':')[1].strip())
                ari = float(lines[3].split(':')[1].strip())

            cd_acc.append({
                'network_id': network_id,
                'order': cd_clusterings_resolutions.index((cd_clustering, cd_resolution)),
                'gt_clustering': gt_clustering,
                'gt_resolution': gt_resolution,
                'cd_clustering': cd_clustering,
                'cd_resolution': cd_resolution,
                'cm': 'without CM',
                'node_coverage': node_coverage,
                'nmi': nmi,
                'ari': ari,
            })

            acc_cm_fp = root / method / gt_clustering / network_id / gt_resolution / \
                '0' / (cd_clustering + '_nofiltcm') / \
                cd_resolution / 'accuracy.txt'
            if not acc_cm_fp.exists():
                print(f'{acc_cm_fp} does not exist')
                continue

            with open(acc_cm_fp) as f:
                lines = list(f.readlines())
                node_coverage_cm = float(lines[1].split(':')[1].strip())
                nmi_cm = float(lines[2].split(':')[1].strip())
                ari_cm = float(lines[3].split(':')[1].strip())

            cd_acc.append({
                'network_id': network_id,
                'order': cd_clusterings_resolutions.index((cd_clustering, cd_resolution)),
                'gt_clustering': gt_clustering,
                'gt_resolution': gt_resolution,
                'cd_clustering': cd_clustering,
                'cd_resolution': cd_resolution,
                'cm': 'with CM',
                'node_coverage': node_coverage_cm,
                'nmi': nmi_cm,
                'ari': ari_cm,
            })

    cd_acc_df = pd.DataFrame(cd_acc)
    return cd_acc_df


networks_list = 'data/networks_val.txt'
cd_acc_df = load_cd_acc_data(root, method, gt_clustering,
                             gt_resolution, cd_clusterings_resolutions, networks_list)
cd_acc_df.to_csv(root / 'cd_acc_both.csv', index=False)

# Make box plots of NMIs with both CM and non-CM
fig, axes = plt.subplots(3, 1, figsize=(10, 8), dpi=150)
plt.rcParams.update({'font.size': 15})

sns.boxplot(
    x='order',
    y='nmi',
    hue='cm',
    data=cd_acc_df,
    notch=True,
    bootstrap=10000,
    ax=axes[0],
)
axes[0].set_xticks([])
axes[0].set_xlabel('')
axes[0].set_ylabel('NMI')
axes[0].legend_.remove()

sns.boxplot(
    x='order',
    y='ari',
    hue='cm',
    data=cd_acc_df,
    notch=True,
    bootstrap=10000,
    ax=axes[1],
)
axes[1].set_xticks([])
axes[1].set_xlabel('')
axes[1].set_ylabel('ARI')
axes[1].legend_.remove()

sns.boxplot(
    x='order',
    y='node_coverage',
    hue='cm',
    data=cd_acc_df,
    notch=True,
    bootstrap=10000,
    ax=axes[2],
)
axes[2].set_xticks(
    range(len(cd_clusterings_resolutions)),
    names,
    # rotation=90,
)
axes[2].set_xlabel('')
axes[2].set_ylabel('Node Coverage')
axes[2].legend_.remove()

handles, labels = axes.flatten()[0].get_legend_handles_labels()
fig.legend(
    handles,
    labels,
    loc='upper center',
    ncols=2,
    bbox_to_anchor=(0.5, 1.05),
    fancybox=True,
)
fig.tight_layout()
fig.savefig(root / 'all_both_boxplot.pdf', bbox_inches='tight')
