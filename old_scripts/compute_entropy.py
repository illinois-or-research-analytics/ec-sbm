import os
import csv
import json

from tqdm import tqdm
import graph_tool.all as gt

# @click.command()
# @click.option("--input-network", required=True, type=click.Path(exists=True), help="Input edgelist")
# @click.option("--input-clustering", required=True, type=click.Path(exists=True), help="Input clustering")
# @click.option("--alternative-clustering", required=False, type=click.Path(exists=True), help="Second clustering")
# @click.option("--input-model", required=True, type=click.Choice(["DC", "Non-DC", "PP"]), help="SBM model")
def calculate_entropy(input_network, input_clustering, alternative_clustering, input_model):
    """This script calculates the entorpy on an input clustering. If alternative clustering is given
    it will calculate the entorpy on that clustering as well and give the statistical test results
    """
    sbm_graph = gt.Graph(directed=False)

    def edge_list_iterable():
        with open(input_network) as f:
            for line in f:
                u, v = line.strip().split()
                yield int(u), int(v)
    vpm_name = sbm_graph.add_edge_list(
        edge_list_iterable(),
        hashed=True,
        hash_type="int",
    )
    gt.remove_self_loops(sbm_graph)
    gt.remove_parallel_edges(sbm_graph)

    old_node_id_to_new_id_map = {}
    for new_id in sbm_graph.iter_vertices():
        old_node_id_to_new_id_map[vpm_name[new_id]] = new_id

    # print('Loading SBM clustering')
    block_label_vertex_property_map = \
        create_block_label_vertex_property_map(
            input_clustering,
            sbm_graph,
            old_node_id_to_new_id_map,
        )

    # print('Loading SBM+CC clustering')
    alternative_block_label_vertex_property_map = \
        create_block_label_vertex_property_map(
            alternative_clustering,
            sbm_graph,
            old_node_id_to_new_id_map,
        )

    return _compute_entropy(input_model, sbm_graph, block_label_vertex_property_map,
                        alternative_block_label_vertex_property_map)


def _compute_entropy(input_model, sbm_graph, block_label_vertex_property_map, alternative_block_label_vertex_property_map):
    if input_model == "DC":
        block_state = gt.BlockState(
            sbm_graph,
            b=block_label_vertex_property_map,
            deg_corr=True,
        )
        entropy_dict = compute_blockstate_entropy(block_state)

        alternative_block_state = gt.BlockState(
            sbm_graph,
            b=alternative_block_label_vertex_property_map,
            deg_corr=True,
        )
        alternative_entropy_dict = compute_blockstate_entropy(
            alternative_block_state)
    elif input_model == "Non-DC":
        block_state = gt.BlockState(
            sbm_graph,
            b=block_label_vertex_property_map,
            deg_corr=False,
        )
        entropy_dict = compute_blockstate_entropy(block_state)
        block_state.draw(output='block_state_nondc.png')

        alternative_block_state = gt.BlockState(
            sbm_graph,
            b=alternative_block_label_vertex_property_map,
            deg_corr=False,
        )
        alternative_entropy_dict = compute_blockstate_entropy(
            alternative_block_state)
        alternative_block_state.draw(
            output='alternative_block_state_nondc.png')
    elif input_model == "PP":
        block_state = gt.PPBlockState(
            sbm_graph,
            b=block_label_vertex_property_map,
        )
        entropy_dict = compute_blockstate_entropy(block_state)

        alternative_block_state = gt.PPBlockState(
            sbm_graph,
            b=alternative_block_label_vertex_property_map,
        )
    else:
        raise ValueError(f"Unknown model: {input_model}")

    # print("SBM Entropy:")
    # pprint.pprint(entropy_dict, sort_dicts=False)
    # print("SBM+CC Entropy:")
    # pprint.pprint(alternative_entropy_dict, sort_dicts=False)

    return entropy_dict, alternative_entropy_dict


def compute_blockstate_entropy(block_state):
    entropy = block_state.entropy(multigraph=False)

    # -log P(A|b, e)
    # for unweighted graphs (or all edges have weight 1)
    # = \sum_r e_r \log n_r - \sum_{r < s} \log e_rs! - \sum_r \log e_rr!!
    # for disconnected components as clusters, e_rs = 0 => \sum_{r < s} \log e_rs! = 0
    adjacency_entropy = \
        block_state.entropy(multigraph=False) \
        - block_state.entropy(adjacency=False, multigraph=False)

    # -log P(b)
    # = log C(N-1, B-1) + log N! + log N - \sum_r log n_r!
    # (error in document, missing the log N term)
    # B small => low entropy
    partition_entropy = \
        block_state.entropy(multigraph=False) \
        - block_state.entropy(partition_dl=False, multigraph=False)

    # -log P(e)
    # = log ((B(B+1)/2, E)) = log (B(B+1)/2 + E - 1, E)
    # B small => low entropy
    edges_entropy = \
        block_state.entropy(multigraph=False) \
        - block_state.entropy(edges_dl=False, multigraph=False)

    # -log P(k)
    # for non-degree corrected models
    # = 0
    # for degree corrected models
    # for kind = 'distributed'
    # = ...
    degree_entropy = \
        block_state.entropy(multigraph=False) \
        - block_state.entropy(degree_dl=False, multigraph=False)

    # # TODO: no idea what this is, always 0.0
    # recs_entropy = \
    #     block_state.entropy(multigraph=False) \
    #     - block_state.entropy(recs_dl=False, multigraph=False)

    entropy_dict = {
        "-log P(A|e,b,k)": adjacency_entropy,
        "-log P(b)": partition_entropy,
        "-log P(k|e,b)": degree_entropy,
        "-log P(e)": edges_entropy,
        "-log P(A,e,b,k)": entropy,
        "is_all": abs(adjacency_entropy + partition_entropy + degree_entropy + edges_entropy - entropy) < 1e-9,
    }

    return entropy_dict


def create_block_label_vertex_property_map(
        input_clustering, 
        sbm_graph, 
        old_node_id_to_new_id_map,
):
    block_label_vertex_property_map = \
        sbm_graph.new_vertex_property("int")

    new_cluster_id = 1
    original_cluster_id_to_new_id_map = {}
    with open(input_clustering, "r") as f:
        for line in f:
            node_id, cluster_id = line.strip().split()
            if cluster_id not in original_cluster_id_to_new_id_map:
                original_cluster_id_to_new_id_map[cluster_id] = new_cluster_id
                new_cluster_id += 1
            block_label_vertex_property_map[
                old_node_id_to_new_id_map[int(node_id)]
            ] = original_cluster_id_to_new_id_map[cluster_id]

    for v in sbm_graph.iter_vertices():
        if block_label_vertex_property_map[v] == 0:
            block_label_vertex_property_map[v] = new_cluster_id
            new_cluster_id += 1

    for v in sbm_graph.iter_vertices():
        assert block_label_vertex_property_map[v] != 0, \
            f"Node {v} does not have a cluster label"

    return block_label_vertex_property_map


if __name__ == "__main__":
    output_fp = 'test.json'
    networks_fp = '/projects/illinois/eng/cs/chackoge/minhyuk2/SBM_estimator/all_empirical_networks_cpp_cc/output/graph_file_path.data'
    dc_clusterings_fp = '/projects/illinois/eng/cs/chackoge/minhyuk2/SBM_estimator/all_empirical_networks_cpp_cc/output/dc_sbm_networks.data'

    if os.path.exists(output_fp):
        with open(output_fp, 'r') as f:
            network_to_entropy = json.load(f)
    else:
        network_to_entropy = dict()

    network_id_to_fp = dict()
    with open(networks_fp, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for network_id, network_fp in csv_reader:
            network_id_to_fp[network_id] = network_fp
    
    with open(dc_clusterings_fp, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        tqdm_pbar = tqdm(csv_reader)
        for network_id, dc_clustering_fp in tqdm_pbar:
            tqdm_pbar.set_description(f'Processing {network_id}')

            if network_id in network_to_entropy:
                continue

            network_fp = network_id_to_fp[network_id]
            dccc_clustering_fp = f'/projects/illinois/eng/cs/chackoge/minhyuk2/SBM_estimator/all_empirical_networks_cpp_cc/output/{network_id}/cpp_cc.clustering'
            try:
                entropy_dict, alt_entropy_dict = calculate_entropy(network_fp, dc_clustering_fp, dccc_clustering_fp, 'DC')
                network_to_entropy[network_id] = {
                    'dc': entropy_dict,
                    'dccc': alt_entropy_dict,
                }

                json.dump(network_to_entropy, open(output_fp, 'w'))
            except Exception as e:
                print(f'Error processing {network_id}: {e}')
                continue
