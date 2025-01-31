import json
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path
import pandas as pd

matplotlib.rcParams.update({'font.size': 18})

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str,
                    default='test.json', help='Input JSON file')
parser.add_argument('--whitelist', type=str,
                    default=None, help='List of networks to include')
parser.add_argument('--blacklist', type=str,
                    default=None, help='List of networks to exclude')
parser.add_argument('--output', type=str,
                    default='output/entropy/', help='Output directory')
args = parser.parse_args()

# Create output directory
output_dir = Path(args.output)
output_dir.mkdir(parents=True, exist_ok=True)

# Load list of whitelist networks
networks_id = [
    line.strip()
    for line in open(args.whitelist, 'r').readlines()
] if args.whitelist else None

# Load list of blacklist networks
blacklist = [
    line.strip()
    for line in open(args.blacklist, 'r').readlines()
] if args.blacklist else None

# Load data
input_fp = args.input
with open(input_fp, 'r') as f:
    data = json.load(f)

# Save list of networks
with open(output_dir / 'orig_networks.txt', 'w') as f:
    f.write('\n'.join(data.keys()))

# Filter out network ids
data = {
    network_id: data[network_id]
    for network_id in data.keys()
    if (networks_id is None or network_id in networks_id) and (blacklist is None or network_id not in blacklist)
}

# Save list of networks
with open(output_dir / 'networks.txt', 'w') as f:
    f.write('\n'.join(data.keys()))

# # check if - log P(A|e,b,k) for dccc is <= - log P(A|e,b,k) for dc
# for network_id, network_data in data.items():
#     if network_data['dccc']['-log P(A|e,b,k)'] > network_data['dc']['-log P(A|e,b,k)']:
#         print(
#             f"Network {network_id} has higher - log P(A|e,b,k) for dccc than dc")

# check if without - log P(e) for dccc is <= - log P(e) for dc
all_networks = set(data.keys())
special_networks = set()
for network_id, network_data in data.items():
    dccc = network_data['dccc']['-log P(A|e,b,k)'] + \
        network_data['dccc']['-log P(k|e,b)'] + \
        network_data['dccc']['-log P(b)']
    dc = network_data['dc']['-log P(A|e,b,k)'] + \
        network_data['dc']['-log P(k|e,b)'] + network_data['dc']['-log P(b)']
    if dccc == dc:
        special_networks.add(network_id)
        print(
            f"Network {network_id} has DL for dccc <= dc without - log P(e): {dccc} <= {dc}")
print(
    f"(A) Networks with higher DL for dccc than dc without -log P(e): {len(special_networks)}")
print(f"Total networks: {len(data)}")
print(f"Ratio: {len(special_networks) / len(data)}")
print(f"Networks - (A): {special_networks}")

# Gather the differences in entropy between dccc and dc for each component
df_data = []
for network_id, network_data in data.items():
    PAebk_dccc = network_data['dccc']['-log P(A|e,b,k)']
    PAebk_dc = network_data['dc']['-log P(A|e,b,k)']
    Pkeb_dccc = network_data['dccc']['-log P(k|e,b)']
    Pkeb_dc = network_data['dc']['-log P(k|e,b)']
    Pe_dccc = network_data['dccc']['-log P(e)']
    Pe_dc = network_data['dc']['-log P(e)']
    Pb_dccc = network_data['dccc']['-log P(b)']
    Pb_dc = network_data['dc']['-log P(b)']

    df_data.append({
        'Network': network_id,
        'Component': '-log P(A|e,b,k)',
        'Difference': PAebk_dccc - PAebk_dc
    })

    df_data.append({
        'Network': network_id,
        'Component': '-log P(k|e,b)',
        'Difference': Pkeb_dccc - Pkeb_dc
    })

    df_data.append({
        'Network': network_id,
        'Component': '-log P(e)',
        'Difference': Pe_dccc - Pe_dc
    })

    df_data.append({
        'Network': network_id,
        'Component': '-log P(b)',
        'Difference': Pb_dccc - Pb_dc
    })

df = pd.DataFrame(df_data)

# Make box plots
fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
sns.boxplot(x='Component', y='Difference', data=df, ax=ax, showfliers=False)
ax.set_xlabel('Component')
ax.set_ylabel('Difference SBM(DC)-CC - SBM(DC)')
ax.axhline(0, color='red', linestyle='--', linewidth=0.1)
plt.tight_layout()
plt.savefig(f'{output_dir}/dccc_vs_dc_entropy_diff_nofliers.pdf')

# Make box plots
fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
sns.boxplot(x='Component', y='Difference', data=df, ax=ax)
ax.set_xlabel('Component')
ax.set_ylabel('Difference SBM(DC)-CC - SBM(DC)')
ax.axhline(0, color='red', linestyle='--', linewidth=0.1)
plt.tight_layout()
plt.savefig(f'{output_dir}/dccc_vs_dc_entropy_diff.eps')

# # check if the sum matches
# for network_id, network_data in data.items():
#     print(f"== Network {network_id}")

#     dccc = network_data['dccc']['-log P(A|e,b,k)'] + network_data['dccc']['-log P(k|e,b)'] + \
#         network_data['dccc']['-log P(e)'] + network_data['dccc']['-log P(b)']
#     dccc_dl = network_data['dccc']['-log P(A,e,b,k)']
#     print(f"Diff: {dccc - dccc_dl}")

#     dc = network_data['dc']['-log P(A|e,b,k)'] + network_data['dc']['-log P(k|e,b)'] + \
#         network_data['dc']['-log P(e)'] + network_data['dc']['-log P(b)']
#     dc_dl = network_data['dc']['-log P(A,e,b,k)']
#     print(f"Diff: {dc - dc_dl}")

#     input()

# # plot - log P(A|e,b,k) for dccc vs dc
# dccc_adjacency_entropy = [network_data['dccc']['-log P(A|e,b,k)'] for network_data in data.values()]
# dc_adjacency_entropy = [network_data['dc']['-log P(A|e,b,k)'] for network_data in data.values()]
# m_dccc, M_dccc = min(dccc_adjacency_entropy), max(dccc_adjacency_entropy)
# m_dc, M_dc = min(dc_adjacency_entropy), max(dc_adjacency_entropy)
# plt.scatter(dc_adjacency_entropy, dccc_adjacency_entropy, alpha=0.5, s=3)
# plt.xlabel('-log P(A|e,b,k) for dc')
# plt.ylabel('-log P(A|e,b,k) for dccc')
# plt.xlim(m_dc, M_dc)
# plt.ylim(m_dccc, M_dccc)
# # plot y = x line
# # plt.plot([m_dc, M_dc], [m_dc, M_dc], color='red', linestyle='--')
# # same axis
# plt.axis('equal')
# plt.tight_layout()
# plt.savefig('dccc_vs_dc.pdf')

# # plot ratio of - log P(A|e,b,k) for DC+CC to DC
# ratio = []
# for network_id, network_data in data.items():
#     if network_data['dc']['-log P(A|e,b,k)'] == 0:
#         print(f"Network {network_id} has - log P(A|e,b,k) for dc equal to 0")
#         # continue
#     if network_data['dccc']['-log P(A|e,b,k)'] == 0:
#         print(f"Network {network_id} has - log P(A|e,b,k) for dccc equal to 0")
#         # continue
#     if network_data['dccc']['-log P(A|e,b,k)'] == network_data['dc']['-log P(A|e,b,k)']:
#         print(
#             f"Network {network_id} has - log P(A|e,b,k) for dccc equal to dc")
#         # continue
#     ratio.append(
#         network_data['dccc']['-log P(A|e,b,k)'] /
#         network_data['dc']['-log P(A|e,b,k)']
#         if network_data['dc']['-log P(A|e,b,k)'] != 0 and network_data['dccc']['-log P(A|e,b,k)'] != 0
#         else 1.0
#     )
# fig, ax = plt.subplots()
# sns.histplot(ratio, ax=ax)
# ax.set_xlabel('Ratio SBM(DC)-CC / SBM(DC)')
# ax.set_ylabel('Frequency')
# ax.set_xlim(0)
# plt.tight_layout()
# plt.savefig(f'{output_dir}/dccc_vs_dc_A_ratio.pdf')

# # plot ratio of - log P(k|e,b) for DC+CC to DC
# ratio = []
# for network_id, network_data in data.items():
#     if network_data['dc']['-log P(k|e,b)'] == 0:
#         print(f"Network {network_id} has - log P(k|e,b) for dc equal to 0")
#         # continue
#     if network_data['dccc']['-log P(k|e,b)'] == 0:
#         print(f"Network {network_id} has - log P(k|e,b) for dccc equal to 0")
#         # continue
#     if network_data['dccc']['-log P(k|e,b)'] == network_data['dc']['-log P(k|e,b)']:
#         print(f"Network {network_id} has - log P(k|e,b) for dccc equal to dc")
#         # continue
#     ratio.append(
#         network_data['dccc']['-log P(k|e,b)'] / network_data['dc']['-log P(k|e,b)']
#         if network_data['dc']['-log P(k|e,b)'] != 0 and network_data['dccc']['-log P(k|e,b)'] != 0
#         else 1.0
#     )
# fig, ax = plt.subplots()
# sns.histplot(ratio, ax=ax)
# ax.set_xlabel('Ratio SBM(DC)-CC / SBM(DC)')
# ax.set_ylabel('Frequency')
# ax.set_xlim(0)
# plt.tight_layout()
# plt.savefig('dccc_vs_dc_k_ratio.pdf')

# # plot ratio of - log P(e) for DC to DC+CC
# ratio = []
# for network_id, network_data in data.items():
#     if network_data['dccc']['-log P(e)'] == 0:
#         print(f"Network {network_id} has - log P(e) for dccc equal to 0")
#         # continue
#     if network_data['dc']['-log P(e)'] == 0:
#         print(f"Network {network_id} has - log P(e) for dc equal to 0")
#         # continue
#     if network_data['dccc']['-log P(e)'] == network_data['dc']['-log P(e)']:
#         print(f"Network {network_id} has - log P(e) for dccc equal to dc")
#         # continue
#     ratio.append(
#         network_data['dc']['-log P(e)'] / network_data['dccc']['-log P(e)']
#         if network_data['dc']['-log P(e)'] != 0 and network_data['dccc']['-log P(e)'] != 0
#         else 1.0
#     )
# fig, ax = plt.subplots()
# sns.histplot(ratio, ax=ax)
# ax.set_xlabel('Ratio SBM(DC) / SBM(DC)-CC')
# ax.set_ylabel('Frequency')
# ax.set_xlim(0)
# plt.tight_layout()
# plt.savefig('dccc_vs_dc_e_ratio.pdf')

# # plot ratio of - log P(b) for DC to DC+CC
# ratio = []
# for network_id, network_data in data.items():
#     if network_data['dccc']['-log P(b)'] == 0:
#         print(f"Network {network_id} has - log P(b) for dccc equal to 0")
#         # continue
#     if network_data['dc']['-log P(b)'] == 0:
#         print(f"Network {network_id} has - log P(b) for dc equal to 0")
#         # continue
#     if network_data['dccc']['-log P(b)'] == network_data['dc']['-log P(b)']:
#         print(f"Network {network_id} has - log P(b) for dccc equal to dc")
#         # continue
#     ratio.append(
#         network_data['dc']['-log P(b)'] / network_data['dccc']['-log P(b)']
#         if network_data['dc']['-log P(b)'] != 0 and network_data['dccc']['-log P(b)'] != 0
#         else 1.0
#     )
# fig, ax = plt.subplots()
# sns.histplot(ratio, ax=ax)
# ax.set_xlabel('Ratio SBM(DC) / SBM(DC)-CC')
# ax.set_ylabel('Frequency')
# ax.set_xlim(0)
# plt.tight_layout()
# plt.savefig('dccc_vs_dc_b_ratio.pdf')

# # plot ratio of -log P(A,e,b,k) for DC to DC+CC
# ratio = []
# for network_id, network_data in data.items():
#     if network_data['dccc']['-log P(A,e,b,k)'] == 0:
#         print(f"Network {network_id} has - log P(A,e,b,k) for dccc equal to 0")
#         # continue
#     if network_data['dc']['-log P(A,e,b,k)'] == 0:
#         print(f"Network {network_id} has - log P(A,e,b,k) for dc equal to 0")
#         # continue
#     if network_data['dccc']['-log P(A,e,b,k)'] == network_data['dc']['-log P(A,e,b,k)']:
#         print(f"Network {network_id} has - log P(A,e,b,k) for dccc equal to dc")
#         # continue
#     ratio.append(
#         network_data['dc']['-log P(A,e,b,k)'] / network_data['dccc']['-log P(A,e,b,k)']
#         if network_data['dc']['-log P(A,e,b,k)'] != 0 and network_data['dccc']['-log P(A,e,b,k)'] != 0
#         else 1.0
#     )
# fig, ax = plt.subplots()
# sns.histplot(ratio, ax=ax)
# ax.set_xlabel('Ratio SBM(DC) / SBM(DC)-CC')
# ax.set_ylabel('Frequency')
# ax.set_xlim(0)
# plt.tight_layout()
# plt.savefig('dccc_vs_dc_DL_ratio.pdf')

# # # plot ratio of - log P(e) for DC+CC to DC
# # ratio = []
# # for network_id, network_data in data.items():
# #     if network_data['dccc']['-log P(e)'] == 0:
# #         print(f"Network {network_id} has - log P(e) for dccc equal to 0")
# #         # continue
# #     if network_data['dc']['-log P(e)'] == 0:
# #         print(f"Network {network_id} has - log P(e) for dc equal to 0")
# #         continue
# #     if network_data['dccc']['-log P(e)'] == network_data['dc']['-log P(e)']:
# #         print(f"Network {network_id} has - log P(e) for dccc equal to dc")
# #         # continue
# #     ratio.append(network_data['dccc']['-log P(e)'] / network_data['dc']['-log P(e)'])
# # fig, ax = plt.subplots()
# # sns.histplot(ratio, ax=ax)
# # ax.set_xlabel('Ratio')
# # ax.set_ylabel('Frequency')
# # ax.set_xlim(0)
# # plt.tight_layout()
# # plt.savefig('dccc_vs_dc_e_ratio_.pdf')

# # # plot ratio of - log P(b) for DC+CC to DC
# # ratio = []
# # for network_id, network_data in data.items():
# #     if network_data['dccc']['-log P(b)'] == 0:
# #         print(f"Network {network_id} has - log P(b) for dccc equal to 0")
# #         # continue
# #     if network_data['dc']['-log P(b)'] == 0:
# #         print(f"Network {network_id} has - log P(b) for dc equal to 0")
# #         continue
# #     if network_data['dccc']['-log P(b)'] == network_data['dc']['-log P(b)']:
# #         print(f"Network {network_id} has - log P(b) for dccc equal to dc")
# #         # continue
# #     ratio.append(network_data['dccc']['-log P(b)'] / network_data['dc']['-log P(b)'])
# # fig, ax = plt.subplots()
# # sns.histplot(ratio, ax=ax)
# # ax.set_xlabel('Ratio')
# # ax.set_ylabel('Frequency')
# # ax.set_xlim(0)
# # plt.tight_layout()
# # plt.savefig('dccc_vs_dc_b_ratio_.pdf')

# # # plot ratio of -log P(A,e,b,k) for DC+CC to DC
# # ratio = []
# # for network_id, network_data in data.items():
# #     if network_data['dccc']['-log P(A,e,b,k)'] == 0:
# #         print(f"Network {network_id} has - log P(A,e,b,k) for dccc equal to 0")
# #         # continue
# #     if network_data['dc']['-log P(A,e,b,k)'] == 0:
# #         print(f"Network {network_id} has - log P(A,e,b,k) for dc equal to 0")
# #         continue
# #     if network_data['dccc']['-log P(A,e,b,k)'] == network_data['dc']['-log P(A,e,b,k)']:
# #         print(f"Network {network_id} has - log P(A,e,b,k) for dccc equal to dc")
# #         # continue
# #     ratio.append(network_data['dccc']['-log P(A,e,b,k)'] / network_data['dc']['-log P(A,e,b,k)'])
# # fig, ax = plt.subplots()
# # sns.histplot(ratio, ax=ax)
# # ax.set_xlabel('Ratio')
# # ax.set_ylabel('Frequency')
# # ax.set_xlim(0)
# # plt.tight_layout()
# # plt.savefig('dccc_vs_dc_DL_ratio_.pdf')
