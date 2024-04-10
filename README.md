### On Campus-Cluster

Install gcc (to run the LFR generator):

```sh
module load gcc
```

Install and configure Julia (to run the ABCD generator):

- Download and install Julia:

```sh
curl -fsSL https://install.julialang.org | sh
```

- Set path for certificate

```sh
export SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt
```

### ABCD generator

To install:

```sh
julia ABCDGraphGenerator.jl/utils/install.jl
```

To modify ABCD generator:

```sh
ln -s /path/to/ABCDGraphGenerator.jl ~/.julia/packages/ABCDGraphGenerator/ZBC5x
```

To generate network:

```
sh gen_network.sh
```

### 