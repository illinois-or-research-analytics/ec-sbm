import os

seed = 0

# Number of nodes
n = 10

# Degree distribution
t1 = 2
d_min = 1
d_max = 2

# Community size distribution
t2 = 3
c_min = 3
c_max = 10

# Mixing parameter
xi = 0.5

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
c_min = "3"
c_max = "4"
c_max_iter = "1000"
xi = "0.2"
islocal = "false"
isCL = "false"
degreefile = "{outdir}/deg.dat"
communitysizesfile = "{outdir}/cs.dat"
communityfile = "{outdir}/com.dat"
networkfile = "{outdir}/edge.dat"
nout = "0"''')
    
os.system(f'julia ABCDGraphGenerator.jl/utils/abcd_sampler.jl {outdir}/config.toml')
