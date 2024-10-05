import json
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

matplotlib.rcParams.update({'font.size': 18})

input_fp = 'test.json'
with open(input_fp, 'r') as f:
    data = json.load(f)

# # check if - log P(A|e,b,k) for dccc is <= - log P(A|e,b,k) for dc
# for network_id, network_data in data.items():
#     if network_data['dccc']['-log P(A|e,b,k)'] > network_data['dc']['-log P(A|e,b,k)']:
#         print(f"Network {network_id} has higher - log P(A|e,b,k) for dccc than dc")

# # check if without - log P(e) for dccc is <= - log P(e) for dc
# list_of_networks = []
# for network_id, network_data in data.items():
#     dccc = network_data['dccc']['-log P(A|e,b,k)'] + network_data['dccc']['-log P(k|e,b)'] + network_data['dccc']['-log P(e)']
#     dc = network_data['dc']['-log P(A|e,b,k)'] + network_data['dc']['-log P(k|e,b)'] + network_data['dc']['-log P(e)']
#     if dccc > dc:
#         list_of_networks.append(network_id)
#         print(f"Network {network_id} has higher DL for dccc than dc without - log P(e)")
# print(f"Total networks with higher DL for dccc than dc without - log P(e): {len(list_of_networks)}")
# print(f"Ratio: {len(list_of_networks) / len(data)}")
# print(f"Networks: {list_of_networks}")

# check if the sum matches
for network_id, network_data in data.items():
    print(f"== Network {network_id}")

    dccc = network_data['dccc']['-log P(A|e,b,k)'] + network_data['dccc']['-log P(k|e,b)'] + network_data['dccc']['-log P(e)'] + network_data['dccc']['-log P(b)']
    dccc_dl = network_data['dccc']['-log P(A,e,b,k)']
    print(f"Diff: {dccc - dccc_dl}")

    dc = network_data['dc']['-log P(A|e,b,k)'] + network_data['dc']['-log P(k|e,b)'] + network_data['dc']['-log P(e)'] + network_data['dc']['-log P(b)']
    dc_dl = network_data['dc']['-log P(A,e,b,k)']
    print(f"Diff: {dc - dc_dl}")

    input()

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
#         print(f"Network {network_id} has - log P(A|e,b,k) for dccc equal to dc")
#         # continue
#     ratio.append(
#         network_data['dccc']['-log P(A|e,b,k)'] / network_data['dc']['-log P(A|e,b,k)']
#         if network_data['dc']['-log P(A|e,b,k)'] != 0 and network_data['dccc']['-log P(A|e,b,k)'] != 0
#         else 1.0
#     )
# fig, ax = plt.subplots()
# sns.histplot(ratio, ax=ax)
# ax.set_xlabel('Ratio SBM(DC)-CC / SBM(DC)')
# ax.set_ylabel('Frequency')
# ax.set_xlim(0)
# plt.tight_layout()
# plt.savefig('dccc_vs_dc_A_ratio.pdf')

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
