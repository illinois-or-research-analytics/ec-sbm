### On Campus-Cluster

Install and configure Julia:

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

To generate network:

```
sh gen_network.sh
```