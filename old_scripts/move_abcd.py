import os
import sys

src = sys.argv[1]
dst = sys.argv[2]

src_dir = f'data/networks/{src}/'
dst_dir = src_dir.replace(src, dst)
# os.makedirs(abcdta_dir, exist_ok=True)
os.system(f'mkdir -p {dst_dir}')
for d in os.listdir(src_dir):
    src_subdir = f'{src_dir}/{d}'
    dst_subdir = src_subdir.replace(src, dst)
    os.system(f'mkdir -p {dst_subdir}')
    # os.makedirs(abcdta_subdir, exist_ok=True)
    for dd in os.listdir(src_subdir):
        src_subsubdir = f'{src_subdir}/{dd}'
        dst_subsubdir = src_subsubdir.replace(src, dst)
        # os.makedirs(abcdta_subsubdir, exist_ok=True)
        os.system(f'mkdir -p {dst_subsubdir}')
        os.system(f'cp {src_subsubdir}/deg.dat {src_subsubdir}/cs.dat {src_subsubdir}/params.json {dst_subsubdir}/')
