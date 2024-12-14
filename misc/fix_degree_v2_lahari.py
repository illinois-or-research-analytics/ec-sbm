import pandas as pd
import numpy as np
import argparse
import os
import time
import logging
import networkit as nk
import psutil
import traceback
import shutil
from scipy.sparse import dok_matrix
import graph_tool.all as gt
from graph_tool.all import *


import warnings
warnings.filterwarnings("ignore")


def read_graph(input_network):
    # Read the network
    elr = nk.graphio.EdgeListReader('\t', 0, continuous=False, directed=False)
    graph = elr.read(input_network)
    graph.removeMultiEdges()
    graph.removeSelfLoops()
    node_mapping_dict = elr.getNodeMap()
    return graph, node_mapping_dict


def read_clustering(input_clustering):
    # Read the clustering
    cluster_df = pd.read_csv(input_clustering, sep="\t", header=None, names=[
                             "node_id", "cluster_name"], dtype=str)
    unique_values = cluster_df['cluster_name'].unique()
    value_map = {
        value: idx
        for idx, value in enumerate(unique_values)
    }
    cluster_df['cluster_id'] = cluster_df['cluster_name'].map(value_map)

    return cluster_df, value_map


def remove_edges(G_c, edges_to_remove):
    for edge in edges_to_remove:
        G_c.removeEdge(edge[0], edge[1])


def add_edges(graph, new_edges):
    for edge in new_edges:
        graph.addEdge(edge[0], edge[1])
    return graph


def get_probs(G_c, node_mapping, cluster_df):
    numerical_to_string_mapping = {v: k for k, v in node_mapping.items()}
    cluster_ids, counts = np.unique(
        cluster_df['cluster_id'], return_counts=True)
    num_clusters = len(cluster_ids)

    node_to_cluster_dict = cluster_df.set_index(
        'node_id')['cluster_id'].to_dict()

    probs = dok_matrix((num_clusters, num_clusters), dtype=int)
    count = 0
    for edge in G_c.iterEdges():
        source = numerical_to_string_mapping.get(edge[0])
        target = numerical_to_string_mapping.get(edge[1])
        source_cluster_idx = node_to_cluster_dict.get(source)
        target_cluster_idx = node_to_cluster_dict.get(target)
        probs[source_cluster_idx, target_cluster_idx] += 1
        probs[target_cluster_idx, source_cluster_idx] += 1

    probs = probs.tocsr(copy=False)
    print("Number of edges as per probs matrix: ",
          probs.trace()//2 + (probs.sum() - probs.trace())//2)
    return probs


def save_generated_graph(edges_list, out_edge_file):
    edge_df = pd.DataFrame(edges_list, columns=['source', 'target'])
    edge_df.to_csv(out_edge_file, sep='\t', index=False, header=None)


def copy_and_append(src_file, dest_file, new_edges):
    if src_file != dest_file:
        shutil.copy(src_file, dest_file)
        print(f"File copied from {src_file} to {dest_file}")

    with open(dest_file, 'a') as f:
        for edge in new_edges:
            f.write(edge[0]+"\t"+edge[1]+"\n")
        print(f"Appended new edges to {dest_file}")


def main(
    edge_input: str,
    cluster_input: str,
    out_edge_file: str,
    emp_edge_input: str
):
    output_dir = os.path.dirname(out_edge_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    probs = None
    generated_graph = None

    log_path = os.path.join(output_dir, f'plusEdges_v2.log')
    print("log path : ", log_path)
    logging.basicConfig(filename=log_path, filemode='w', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    job_start_time = time.time()

    def log_cpu_ram_usage(step_name):
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        logging.info(f"Step: {step_name} | CPU Usage: {cpu_percent}% | RAM Usage: {
                     ram_percent}% | Disk Usage: {disk_percent}")

    try:
        log_cpu_ram_usage("Start")
        logging.info("Reading empirical graph...")
        start_time = time.time()
        emp_graph, emp_node_mapping = read_graph(emp_edge_input)
        logging.info(f"Time taken: {round(
            time.time() - start_time, 3)} seconds")
        print("Number of nodes in the empirical network : ",
              emp_graph.numberOfNodes())
        print("Number of edges in the empirical network : ",
              emp_graph.numberOfEdges())

        log_cpu_ram_usage("After reading empirical graph!")
        logging.info("Reading graph clustering:")
        start_time = time.time()
        cluster_df, cluster_mapping_dict = read_clustering(cluster_input)
        # -- clustering_dict  = {node_id : cluster_iid} --
        clustering_dict = dict(
            zip(
                cluster_df['node_id'],
                cluster_df['cluster_id'],
            )
        )

        logging.info(f"Time taken: {round(
            time.time() - start_time, 3)} seconds")
        log_cpu_ram_usage("After reading clustering data!")

        logging.info("Get edge probs matrix for empirical network!")
        start_time = time.time()
        emp_clustered_nodes = [emp_node_mapping[v]
                               for v in clustering_dict.keys()]
        G_c = nk.graphtools.subgraphFromNodes(emp_graph, emp_clustered_nodes)
        emp_probs = get_probs(G_c, emp_node_mapping, cluster_df)
        logging.info(f"Time taken: {round(
            time.time() - start_time, 3)} seconds")

        logging.info("Starting the iterations! ")
        input_filepath = edge_input
        continue_iterations = True
        iteration_count = 1
        while continue_iterations and iteration_count <= 1:
            logging.info(f"Current Iteration : {iteration_count}")
            itr_start_time = time.time()
            logging.info("Reading input graph...")
            start_time = time.time()
            graph, node_mapping = read_graph(input_filepath)
            logging.info(f"Time taken: {round(
                time.time() - start_time, 3)} seconds")
            print("Number of nodes in the network : ", graph.numberOfNodes())
            print("Number of edges in the network : ", graph.numberOfEdges())
            log_cpu_ram_usage("After reading graph!")

            clustered_nodes = [node_mapping[v] for v in clustering_dict.keys()]
            node_mapping_reversed = {u: str(v)
                                     for v, u in node_mapping.items()}

            logging.info("Finding nodes with available degrees")
            start_time = time.time()
            # Find clustered nodes with degree less than expected
            emp_degrees = dict()
            sbm_degrees = dict()
            available_node_degrees = dict()
            for c_node in clustering_dict.keys():
                emp_node = emp_node_mapping[c_node]
                syn_node = node_mapping[c_node]
                emp_degrees[c_node] = emp_graph.degree(emp_node)
                sbm_degrees[c_node] = graph.degree(syn_node)
                deg_diff = emp_degrees[c_node]-sbm_degrees[c_node]
                if (deg_diff > 0):
                    available_node_degrees[syn_node] = deg_diff

            logging.info(f"Time taken: {round(
                time.time() - start_time, 3)} seconds")

            logging.info("Get edge probs matrix for synthetic network!")
            start_time = time.time()
            G_c_wc = nk.graphtools.subgraphFromNodes(graph, clustered_nodes)
            edge_perc = abs(G_c.numberOfEdges() -
                            G_c_wc.numberOfEdges()) / G_c.numberOfEdges() * 100
            if edge_perc < 1:
                continue_iterations = False
            sbm_wc_probs = get_probs(G_c_wc, node_mapping, cluster_df)
            logging.info(f"Time taken: {round(
                time.time() - start_time, 3)} seconds")

            logging.info("Get probs matrix for remaining edges!")
            start_time = time.time()
            probs = emp_probs - sbm_wc_probs
            # set negative values to 0 to avoid adding more edges which already are more than needed.
            probs.data[probs.data < 0] = 0

            # # Set all diagonal values to zero to avoid inter cluster edges
            # diagonal_indices = np.arange(probs.shape[0])
            # probs[diagonal_indices, diagonal_indices] = 0

            # print(probs)
            logging.info(f"Time taken: {round(
                time.time() - start_time, 3)} seconds")

            logging.info("Use generate sbm function on available nodes!")
            start_time = time.time()
            # Get all the nodes with available degrees
            # available_node_set = set(available_node_degrees.keys())
            total_available_nodes = len(available_node_degrees.keys())
            available_nodes_list = []
            available_degrees = []
            for node, degree in available_node_degrees.items():
                available_nodes_list.append(node)
                available_degrees.append(min(total_available_nodes-1, degree))

            avail_nodes_block_assignment = []
            for syn_node in available_nodes_list:
                avail_nodes_block_assignment.append(
                    clustering_dict[node_mapping_reversed[syn_node]])

            clusters_to_be_considered = np.unique(avail_nodes_block_assignment)
            for i in range(probs.shape[0]):
                for ind in range(probs.indptr[i], probs.indptr[i + 1]):
                    j = probs.indices[ind]
                    if i not in clusters_to_be_considered:
                        probs.data[ind] = 0
                    if j not in clusters_to_be_considered:
                        probs.data[ind] = 0

            print(f'Total available nodes : {total_available_nodes}, length of block assignment : {len(
                avail_nodes_block_assignment)}, length of available nodes list : {len(available_nodes_list)}')
            total_avail_edges = probs.trace()//2 + (probs.sum() - probs.trace())//2
            total_degrees = sum(available_degrees)//2
            print(total_avail_edges, total_degrees)
            # print(available_degrees)

            if total_avail_edges > 0 and total_degrees > 0:
                generated_graph = gt.generate_sbm(avail_nodes_block_assignment, probs, available_degrees,
                                                  directed=False)

                gt.remove_parallel_edges(generated_graph)
                gt.remove_self_loops(generated_graph)
                print(f"Total number of edges added : {
                      generated_graph.num_edges()}")
                logging.info(f"Total number of edges added : {
                             generated_graph.num_edges()}")
            logging.info(f"Time taken: {round(
                time.time() - start_time, 3)} seconds")
            logging.info("Save the new graph!")
            start_time = time.time()
            new_edges = set()
            if generated_graph is not None:
                for edge in generated_graph.iter_edges():
                    node1 = node_mapping_reversed[available_nodes_list[edge[0]]]
                    node2 = node_mapping_reversed[available_nodes_list[edge[1]]]
                    new_edges.add((node1, node2))
            copy_and_append(input_filepath, out_edge_file, new_edges)
            logging.info(f"Time taken: {round(
                time.time() - start_time, 3)} seconds")

            input_filepath = out_edge_file
            iteration_count += 1
            if len(new_edges) == 0:
                continue_iterations = False
            logging.info(f"Time taken for this iteration: {
                         round(time.time() - itr_start_time, 3)} seconds")
        logging.info(f"Total Time taken: {round(
            time.time() - job_start_time, 3)} seconds")
        log_cpu_ram_usage("Usage statistics after job completion!")

    except Exception as e:
        print(e)
        traceback.print_exc()
        logging.error("Exception occurred", exc_info=True)


def parse_args():
    parser = argparse.ArgumentParser(description='Generate graph ')
    parser.add_argument(
        '-f', metavar='edge_list_filepath', type=str, required=True,
        help='network edge_list filepath'
    )
    parser.add_argument(
        '-c', metavar='clustering_filepath', type=str, required=True,
        help='network clustering filepath'
    )
    parser.add_argument(
        '-oe', metavar='out_edge_file', type=str, required=False,
        help='output edgelist path'
    )
    parser.add_argument(
        '-ef', metavar='emp_edge_input', type=str, required=True,
        help='empirical network edgelist path'
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    main(args.f, args.c, args.oe, args.ef)
