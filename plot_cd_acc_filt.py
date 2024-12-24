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
    network_ids = [
        line.strip() for line in open(networks_list)
    ]

    cd_acc = []
    for network_id in network_ids:
        for cd_clustering, cd_resolution in cd_clusterings_resolutions:
            acc_fp = root / method / gt_clustering / network_id / gt_resolution / \
                '0' / cd_clustering / cd_resolution
            if not acc_fp.exists():
                print(f'{acc_fp} does not exist')
                continue

            with open(acc_fp) as f:
                lines = list(f.readlines())
                node_coverage = float(lines[1].split(':')[1].strip())
                nmi = float(lines[2].split(':')[1].strip())
                ari = float(lines[3].split(':')[1].strip())

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
                'node_coverage': node_coverage,
                'nmi': nmi,
                'ari': ari,
                'node_coverage_cm': node_coverage_cm,
                'nmi_cm': nmi_cm,
                'ari_cm': ari_cm,
            })

    cd_acc_df = pd.DataFrame(cd_acc)
    return cd_acc_df


network_sizes = {
    'large': 'data/networks_val_large.txt',
    'medium': 'data/networks_val_medium.txt',
    'small': 'data/networks_val_small.txt'
}

combined_df = pd.DataFrame()

for size, networks_list in network_sizes.items():
    cd_acc_df = load_cd_acc_data(root, method, gt_clustering, gt_resolution,
                                 cd_clusterings_resolutions, networks_list)
    cd_acc_df['size'] = size
    combined_df = pd.concat([combined_df, cd_acc_df], ignore_index=True)

combined_df.to_csv(root / 'cd_acc_combined.csv', index=False)


# Sort rows so that clustering and resolution are in the same order
combined_df = combined_df.sort_values(['cd_clustering', 'cd_resolution'])

fig, axes = plt.subplots(3, 1, figsize=(10, 8), dpi=150)

# Make box plots of the changes in NMI from CM
combined_df['nmi_diff'] = combined_df['nmi_cm'] - combined_df['nmi']
sns.boxplot(
    x='order',
    y='nmi_diff',
    hue='size',
    data=combined_df,
    notch=True,
    ax=axes[0]
)
axes[0].axhline(0.0, color='red', linestyle='dotted')
axes[0].set_xticks([])
# axes[0].set_xticklabels(names, rotation=90)
axes[0].set_xlabel('')
axes[0].set_ylabel('NMI Change')

# Make box plots of the changes in ARI from CM
combined_df['ari_diff'] = combined_df['ari_cm'] - combined_df['ari']
sns.boxplot(
    x='order',
    y='ari_diff',
    hue='size',
    data=combined_df,
    notch=True,
    ax=axes[1]
)
axes[1].axhline(0.0, color='red', linestyle='dotted')
axes[1].set_xticks([])
# axes[1].set_xticklabels(names, rotation=90)
axes[1].set_xlabel('')
axes[1].set_ylabel('ARI Change')

# Make box plots of the changes in node coverage from CM
combined_df['node_coverage_diff'] = combined_df['node_coverage_cm'] - \
    combined_df['node_coverage']
sns.boxplot(
    x='order',
    y='node_coverage_diff',
    hue='size',
    data=combined_df,
    notch=True,
    ax=axes[2]
)
axes[2].axhline(0.0, color='red', linestyle='dotted')
axes[2].set_xticks(range(len(cd_clusterings_resolutions)))
axes[2].set_xticklabels(names)
axes[2].set_xlabel('')
axes[2].set_ylabel('Node Coverage Change')

plt.tight_layout()
plt.savefig(root / f'cd_acc_diff_bin_boxplots.pdf')
