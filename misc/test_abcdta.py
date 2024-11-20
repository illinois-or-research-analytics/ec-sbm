import os

seed = 1

# Number of nodes
n = 8

# Degree distribution
t1 = 2
d_min = 3
d_max = 3

# Community size distribution
t2 = 3
c_min = 8
c_max = 8

# Mixing parameter
xi = 0.0

outdir = 'output/test'
os.makedirs(outdir, exist_ok=True)

with open(f'{outdir}/config.toml', 'w') as f:
    f.write(f'''seed = "{seed}"
n = "{n}"
t1 = "{t1}"
d_min = "{d_min}"
d_max = "{d_max}"
d_max_iter = "1000"
t2 = "{t2}"
c_min = "{c_min}"
c_max = "{c_max}"
c_max_iter = "1000"
xi = "{xi}"
islocal = "false"
isCL = "false"
degreefile = "{outdir}/deg.dat"
communitysizesfile = "{outdir}/cs.dat"
communityfile = "{outdir}/com.dat"
networkfile = "{outdir}/edge.dat"
nout = "0"''')

os.system(
    f'julia ABCDGraphGenerator.jl/utils/abcdtadev_sampler.jl {outdir}/config.toml')
