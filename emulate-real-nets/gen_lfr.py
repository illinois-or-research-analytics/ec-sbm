import multiprocessing as mp
import subprocess
import sys
import json
import argparse
import os


def gen_lfr(stats_path, lfr_path, cmin):
    with open(stats_path) as f:
        net_cluster_stats = json.load(f)
    base_path = os.getcwd()
    lfr_net_dir = stats_path.replace('.json', '')+"_lfr_"+cmin
    if not os.path.exists(lfr_net_dir):
        os.system('mkdir ' + lfr_net_dir)
    os.chdir(lfr_net_dir)
    if int(cmin) > net_cluster_stats['max-cluster-size']:
        return
    if net_cluster_stats['node-count'] > 5000000:
        ratio = net_cluster_stats['node-count'] / 3000000
        net_cluster_stats['node-count'] = 3000000
        net_cluster_stats['max-degree'] = int(net_cluster_stats['max-degree'] / ratio)
        net_cluster_stats['max-cluster-size'] = int(net_cluster_stats['max-cluster-size'] / ratio)
        net_cluster_stats['max-cluster-size'] = 1000
    if net_cluster_stats['mean-degree'] < 4:
        net_cluster_stats['max-degree'] = 31
    if net_cluster_stats['max-degree'] > 1000:
       net_cluster_stats['max-degree'] = 1000
    if net_cluster_stats['max-cluster-size'] > 5000:
       net_cluster_stats['max-cluster-size'] = 5000
    if net_cluster_stats['mean-degree'] > 50:
       net_cluster_stats['max-cluster-size'] = 1000
    cmd = base_path+'/'+lfr_path+ ' -N ' + str(net_cluster_stats['node-count']) \
                            + ' -k ' + str(net_cluster_stats['mean-degree']) \
                            + ' -maxk ' + str(net_cluster_stats['max-degree']) \
                            + ' -mu ' + str(net_cluster_stats['mixing-parameter']) \
                            + ' -maxc ' + str(net_cluster_stats['max-cluster-size']) \
                            + ' -minc ' + cmin \
                            + ' -t1 ' + str(net_cluster_stats['tau1']) \
                            + ' -t2 ' + str(net_cluster_stats['tau2'])
    print(cmd)
    os.system(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Emulating real networks using LFR graphs.')
    parser.add_argument('-n', metavar='net', type=str, required=True,
                        help='network clustering statistics file path (json format)')
    parser.add_argument('-lp', metavar='lfrpath', type=str, required=True,
                        help='LFR software executable path (benchmark)')
    parser.add_argument('-cm', metavar='cmin', type=str, required=False,
                        help='Minimum community size')
    args = parser.parse_args()
    gen_lfr(args.n, args.lp, args.cm if args.cm else str(1))
