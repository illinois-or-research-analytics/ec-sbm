# Emulating real networks with LFR graphs
We provide scripts for estimating the parameters of a network and a clustering of that network, and generating a synthetic LFR graph ([Lancichinetti et al., 2008](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.78.046110)) that attempts to resemble the characteristics of this network/clustering pair. These scripts are used in the following paper for emulating real networks using LFR graphs:

M. Park, Y. Tabatabaee, B. Liu, V. Kamath Pailodi, V. Ramavarapu, R. Ramachandran, D. Korobskiy, F. Ayres, G. Chacko, T. Warnow. Well-Connected Communities in Real-World Networks. [https://arxiv.org/abs/2303.02813.](https://arxiv.org/abs/2303.02813)

## Dependencies
These scripts are implemented in Python 3 and have the following dependencies:
- [LFR benchmark graph software](https://www.santofortunato.net/resources)
- [Python 3.x](https://www.python.org)
- [NetworkX](https://networkx.org)
- [Numpy](https://numpy.org)
- [powerlaw](https://pypi.org/project/powerlaw/)
- [NetworKit](https://networkit.github.io/) (for large networks only)

If you have Python 3 and pip, you can use `pip install -r requirements.txt` to install the other dependencies. We provide the LFR benchmark software binary files for MacOS and Linux in `binary_networks` directory, but the software can also be downloaded and compiled from [https://www.santofortunato.net/resources](https://www.santofortunato.net/resources).

## Usage Instructions

### Estimating parameters of a network/clustering pair
**Input:** A file containing a network edge-list and a file containing clustering memberships on the same network.
```
$ python3 estimate_properties.py -n <network_edgelist.tsv> -c <clustering_memberships.tsv>
```
**Output:** A JSON file named `<clustering_memberships.json>` (located in the *input clustering directory*) that provides information shown in the following example.

**Example:** We use the [arXiv High energy physics citation network](http://snap.stanford.edu/data/cit-HepPh.html) from the [SNAP collection](http://snap.stanford.edu/index.html) and a Leiden clustering of it (with `r=0.01`) as an example input:
```
$ python3 estimate_properties.py -n example/cit_hepph_cleaned.tsv -c example/cit_hepph_leiden.01.tsv
```
```
{
    "node-count": 34546,
    "edge-count": 420877,
    "isolate-count": 0,
    "num-connected-components": 61,
    "max-connected-components": 34401,
    "min-degree": 1,
    "max-degree": 846,
    "mean-degree": 24.36617842876165,
    "median-degree": 15.0,
    "num-clusters": 2136,
    "min-cluster-size": 1,
    "max-cluster-size": 800,
    "mean-cluster-size": 16.173220973782772,
    "median-cluster-size": 1.0,
    "num-singletons": 1322,
    "num-non-singletons": 814,
    "modularity-score": 0.5992111149783027,
    "node-coverage": 0.9617321831760551,
    "mixing-parameter": 0.37999943730019126,
    "tau1": 3.6312283315636975,
    "xmin1": 85.0,
    "tau2": 1.8497807268067572,
    "xmin2": 23.0,
    "tau1-fixed": 1.2997088572994,
    "xmin1-fixed": 1.0,
    "tau2-fixed": 1.622200259246516,
    "xmin2-fixed": 1.0
}
```
### Emulating a network/clustering with LFR graphs
**Input:** A JSON file as generated in the previous step, path to the LFR software executable and a minimum community size (for most networks, we do not suggest using values less than 10 for `cmin`, as LFR software may not able to generate the graph in a reasonable time).

**Output:** A directory with the LFR network edge-list (`network.dat`) and its ground-truth community memberships (`community.dat`), as well as statistics of the LFR network/communities (`statistics.dat`).

```
$ python3 gen_lfr.py -n <clustering_memberships.json> -lp <lfr-benchmark-software-path> -cm <cmin_value>
```

The LFR output files will be located in a directory called `<clustering_memberships>_lfr_<cmin>` and the log of the LFR software will be printed out.

**Note**: The LFR software binary for MacOS is `binary_networks/lfr_mac` and the binary file for Linux systems is `binary_networks/lfr_linux`.

**Example:**
```
$ python3 gen_lfr.py -n example/cit_hepph_leiden.01.json -lp binary_networks/lfr_linux -cm 20 > example/cit_hepph_leiden.01.log
```
```
./binary_networks/benchmark -N 34546 -k 24.36617842876165 -maxk 846 -mu 0.37999943730019126 -maxc 800 -minc 20 -t1 3.6312283315636975 -t2 1.8497807268067572
setting... -N 34546
setting... -k 24.36617842876165
setting... -maxk 846
setting... -mu 0.37999943730019126
setting... -maxc 800
setting... -minc 20
setting... -t1 3.6312283315636975
setting... -t2 1.8497807268067572

**************************************************************
number of nodes:	34546
average degree:	24.3662
maximum degree:	846
exponent for the degree distribution:	3.63123
exponent for the community size distribution:	1.84978
mixing parameter:	0.379999
number of overlapping nodes:	0
number of memberships of the overlapping nodes:	0
community size range set equal to [20 , 800]
**************************************************************

building communities...
connecting communities...
recording network...


---------------------------------------------------------------------------
network of 34546 vertices and 429828 edges;	 average degree = 24.8844

average mixing parameter: 0.379969 +/- 0.0194945
p_in: 0.368457	p_out: 0.00025681
```
### Handling large networks
For very large networks (e.g. with more than 100 million edges), the `estimate_properties.py` script can be slow and have high memory usage. For these networks, we suggest using `estimate_properties_networkit.py` instead, that uses `NetworKit` library which is more scalable than `NetworkX`. The I/O format is similar, but the network nodes should be labeled 0 to $n-1$. Also, the LFR graph software is not scalable to large networks (more than 10 million nodes) and even for small networks, it may not successfully produce a network with the given properties in a reasonable time in some cases (e.g. when the mixing parameter is very high). The `gen_lfr.py` script reduces the size of large networks to 3 million nodes while keeping the density (average degree) and other characteristics intact. In some cases, it also varies the ranges of community sizes to increase the chances of successfuly producing an output.
