import typer
import networkit as nk
import pandas as pd
import os

from enum import Enum
from numpy import log10

from hm01.clusterers.abstract_clusterer import AbstractClusterer
from hm01.clusterers.ikc_wrapper import IkcClusterer
from hm01.clusterers.leiden_wrapper import LeidenClusterer, Quality
from hm01.graph import Graph, IntangibleSubgraph, RealizedSubgraph
from hm01.mincut import viecut

class ClustererSpec(str, Enum):
    """ (VR) Container for Clusterer Specification """  
    leiden = "leiden"
    ikc = "ikc"
    leiden_mod = "leiden_mod"

def main(
    input: str = typer.Option(..., "--input", "-i"),
    existing_clustering: str = typer.Option(..., "--existing-clustering", "-e"),
    clusterer_spec: ClustererSpec = typer.Option(..., "--clusterer", "-c"),
    k: int = typer.Option(-1, "--k", "-k"),
    resolution: float = typer.Option(-1, "--resolution", "-g"),

): 
    base, ext = os.path.splitext(existing_clustering)
    outfile = base + '_stats.csv'

    df = pd.read_csv(outfile)
    k_vals = list(df['ktruss_vals'])

    outfile = base + '_ktruss.csv'

    print("Loading clusters...")
    # (VR) Check -g and -k parameters for Leiden and IKC respectively
    if clusterer_spec == ClustererSpec.leiden:
        assert resolution != -1, "Leiden requires resolution"
        clusterer = LeidenClusterer(resolution)
    elif clusterer_spec == ClustererSpec.leiden_mod:
        assert resolution == -1, "Leiden with modularity does not support resolution"
        clusterer = LeidenClusterer(resolution, quality=Quality.modularity)
    else:
        assert k != -1, "IKC requires k"
        clusterer = IkcClusterer(k)

    clusters = clusterer.from_existing_clustering(existing_clustering)
    ids = [cluster.index for cluster in clusters]
    ns = [cluster.n() for cluster in clusters]
    print("Done")

    print("Loading graph...")
    # (VR) Load full graph into Graph object
    edgelist_reader = nk.graphio.EdgeListReader("\t", 0)
    nk_graph = edgelist_reader.read(input)

    global_graph = Graph(nk_graph, "")
    ms = [cluster.count_edges(global_graph) for cluster in clusters]
    print("Done")

    print("Realizing clusters...")
    clusters = [cluster.realize(global_graph) for cluster in clusters]
    print("Done")

    print("Getting k-truss nodes...")
    ktruss_nodes = [cluster.retrieve_ktruss_nodes(k_vals[i]) for i, cluster in enumerate(clusters)]
    print("Done")

    print("Reformatting lists...")
    col_1 = []
    col_2 = []
    col_3 = []
    for i, ktruss_l in enumerate(ktruss_nodes):
        col_1 = col_1 + [clusters[i].index for _ in range(len(ktruss_l))]
        col_2 = col_2 + [k_vals[i] for _ in range(len(ktruss_l))]
        col_3 = col_3 + ktruss_l
    print("Done")

    print("Writing to output file...")
    df = pd.DataFrame(list(zip(col_1, col_2, col_3)),
               columns =['cluster', 'ktruss_vals', 'ktruss_nodes'])
    df.to_csv(outfile, index=False)
    print("Done")


def entry_point():
    typer.run(main)

if __name__ == "__main__":
    entry_point()