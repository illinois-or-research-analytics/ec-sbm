import os
import argparse
import networkit as nk
import powerlaw
import numpy as np
import json
from collections import defaultdict
import matplotlib.pyplot as plt


def membership_to_partition(membership):
    part_dict = {}
    for index, value in membership.items():
        if value in part_dict:
            part_dict[value].append(index)
        else:
            part_dict[value] = [index]
    return part_dict.values()


def plot_dist(dist, name):
    plt.cla()
    plt.grid(linestyle='--', linewidth=0.5)
    x = np.arange(1, len(dist)+1)
    plt.plot(np.log(x), np.log(dist), color='black')
    plt.ylabel('ln (dist)')
    plt.savefig(name+'_dist.pdf')


def get_membership_list_from_file(net, file_name):
    membership = dict()
    with open(file_name) as f:
        for line in f:
            i, m = line.strip().split()
            if net.hasNode(int(i)):
                membership[int(i)] = m
    return membership


def write_membership_list_to_file(file_name, membership):
    with open(file_name, 'w') as f:
        f.write(
            '\n'.join(str(i)+' '+str(membership[i]+1) for i in range(len(membership))))


def compute_mixing_param(net, membership):
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    for n1, n2 in net.iterEdges():
        if membership[n1] == membership[n2]:  # nodes are co-clustered
            in_degree[n1] += 1
            in_degree[n2] += 1
        else:
            out_degree[n1] += 1
            out_degree[n2] += 1
    mus = [out_degree[i]/(out_degree[i]+in_degree[i]) if (out_degree[i] +
                                                          in_degree[i]) != 0 else 0 for i in net.iterNodes()]
    mixing_param = np.mean(mus)
    return mixing_param


def compute_xi(net, membership):
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    for n1, n2 in net.iterEdges():
        if membership[n1] == membership[n2]:  # nodes are co-clustered
            in_degree[n1] += 1
            in_degree[n2] += 1
        else:
            out_degree[n1] += 1
            out_degree[n2] += 1
    outs = [out_degree[i] for i in net.iterNodes()]
    xi = np.sum(outs) / 2 / net.numberOfEdges()
    return xi


def clustering_statistics(net, membership, show_cluster_size_dist=False):
    partition = membership_to_partition(membership)
    cluster_num = len(partition)
    cluster_sizes = [len(c) for c in partition]
    min_size, max_size, mean_size, median_size = int(np.min(cluster_sizes)), int(np.max(cluster_sizes)), \
        np.mean(cluster_sizes), np.median(cluster_sizes)
    singletons_num = cluster_sizes.count(1)
    non_singleton_num = cluster_num - singletons_num
    # modularity_score = modularity(net, partition)
    # modularity_score = nk.community.Modularity().getQuality(partition, net)
    node_count = net.numberOfNodes()
    coverage = (node_count - singletons_num) / node_count
    print('#clusters in partition:', cluster_num)
    if show_cluster_size_dist:
        print(cluster_sizes)
    print('min, max, mean, median cluster sizes:',
          min_size, max_size, mean_size, median_size)
    print('number of singletons:', singletons_num)
    print('number of non-singleton clusters:', non_singleton_num)
    # print('modularity:', modularity_score)
    print('coverage:', coverage)
    return cluster_num, cluster_sizes, min_size, max_size, mean_size, median_size, singletons_num, \
        non_singleton_num, coverage


def network_statistics(graph, show_connected_components=False):
    node_count, edge_count = graph.numberOfNodes(), graph.numberOfEdges()
    # isolate_count = len(list(nx.isolates(graph)))
    cc = nk.components.ConnectedComponents(graph)
    cc.run()
    compSizes = cc.getComponentSizes()
    connected_component_num = len(compSizes)
    max_connected_component = max(compSizes.values())
    # connected_components_sizes = [len(c) for c in nx.connected_components(graph)]
    # connected_component_num = len(connected_components_sizes)
    # max_connected_component = max(connected_components_sizes)
    degrees = [net.degree(v) for v in net.iterNodes()]
    isolate_count = degrees.count(0)
    # degrees = [d for _, d in graph.degree()]
    min_degree, max_degree, mean_degree, median_degree = int(np.min(degrees)), int(np.max(degrees)), \
        np.mean(degrees), np.median(degrees)
    print('#nodes, #edges, #isolates:', node_count, edge_count, isolate_count)
    print('num connected comp:', connected_component_num)
    print('max connected comp:', max_connected_component)
    if show_connected_components:
        print(sorted(compSizes, reverse=True))
    print('min, max, mean, median degree:', min_degree,
          max_degree, mean_degree, median_degree)
    return node_count, edge_count, degrees, isolate_count, connected_component_num, max_connected_component, \
        min_degree, max_degree, mean_degree, median_degree


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Estimating properties of a network/clustering pair.')
    parser.add_argument('-n', metavar='net', type=str, required=True,
                        help='network edge-list path')
    parser.add_argument('-c', metavar='clustering', type=str, required=True,
                        help='clustering membership path')
    parser.add_argument('-o', metavar='output', type=str, required=True,
                        help='output filename')
    args = parser.parse_args()

    print('- properties of the input network')
    # net = nx.read_edgelist(args.n, nodetype=int)
    net = nk.readGraph(args.n, nk.Format.EdgeListTabZero)
    node_count, edge_count, degrees, isolate_count, connected_component_num, max_connected_component, \
        min_degree, max_degree, mean_degree, median_degree = network_statistics(
            net)

    print('\n- properties of the input clustering')
    membership = get_membership_list_from_file(net, args.c)
    print(len(membership))
    cluster_num, cluster_sizes, min_size, max_size, mean_size, median_size, singletons_num, non_singleton_num, \
        coverage = clustering_statistics(net, membership)

    degree_dist = powerlaw.Fit(degrees, discrete=True)
    tau1 = degree_dist.power_law.alpha
    xmin1 = degree_dist.power_law.xmin

    degree_dist_fixed = powerlaw.Fit(degrees, discrete=True, xmin=min_degree)
    tau1_fixed = degree_dist_fixed.power_law.alpha
    xmin1_fixed = degree_dist_fixed.power_law.xmin

    # powerlaw.plot_pdf(community_sizes, color='b')

    community_size_dist = powerlaw.Fit(cluster_sizes, discrete=True)
    tau2 = community_size_dist.power_law.alpha
    xmin2 = community_size_dist.power_law.xmin

    community_size_dist_fixed = powerlaw.Fit(
        cluster_sizes, discrete=True, xmin=min_size)
    tau2_fixed = community_size_dist_fixed.power_law.alpha
    xmin2_fixed = community_size_dist_fixed.power_law.xmin

    mu = compute_mixing_param(net, membership)
    xi = compute_xi(net, membership)

    print('mixing parameter (mu):', mu)
    print('mixing parameter (xi):', xi)
    print('tau1, xmin1, tau2, xmin2', tau1, xmin1, tau2, xmin2)
    print('tau1, xmin1, tau2, xmin2 [fixed xmin]',
          tau1_fixed, xmin1_fixed, tau2_fixed, xmin2_fixed)

    net_cluster_stats = {
        "node-count": node_count,
        "edge-count": edge_count,
        "isolate-count": isolate_count,
        "num-connected-components": connected_component_num,
        "max-connected-components": max_connected_component,
        "min-degree": min_degree,
        "max-degree": max_degree,
        "mean-degree": mean_degree,
        "median-degree": median_degree,
        "num-clusters": cluster_num,
        "min-cluster-size": min_size,
        "max-cluster-size": max_size,
        "mean-cluster-size": mean_size,
        "median-cluster-size": median_size,
        "num-singletons": singletons_num,
        "num-non-singletons": non_singleton_num,
        "node-coverage": coverage,
        "mixing-parameter": mu,
        "xi": xi,
        "tau1": tau1,
        "xmin1": xmin1,
        "tau2": tau2,
        "xmin2": xmin2,
        "tau1-fixed": tau1_fixed,
        "xmin1-fixed": xmin1_fixed,
        "tau2-fixed": tau2_fixed,
        "xmin2-fixed": xmin2_fixed
    }

    with open(args.o, "w") as f:
        json_object = json.dumps(net_cluster_stats, indent=4)
        f.write(json_object)
