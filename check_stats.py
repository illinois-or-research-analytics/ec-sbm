import os

root = 'data/stats'

for method in os.listdir(root):
    if method not in ['orig']:
        continue

    for clustering in os.listdir(os.path.join(root, method)):
        for dataset in os.listdir(os.path.join(root, method, clustering)):
            for resolution in os.listdir(os.path.join(root, method, clustering, dataset)):
                path = os.path.join(
                    root, method, clustering, dataset, resolution)
                if not os.path.exists(path):
                    print(f'[ERROR] {path} does not exist')
                    continue

                if not os.path.exists(os.path.join(path, 'done')):
                    print(f'[ERROR] {path} is not done computing stats')

for method in os.listdir(root):
    if method not in ['sbmmcsprev1+o+e2', 'sbmmcsprev1+eL2+o']:
        continue

    for clustering in os.listdir(os.path.join(root, method)):
        if clustering in []:  # ['ikc_cm', 'leiden_mod_cm']:
            continue

        for dataset in os.listdir(os.path.join(root, method, clustering)):
            for resolution in os.listdir(os.path.join(root, method, clustering, dataset)):
                for i in range(1):
                    path = os.path.join(
                        root, method, clustering, dataset, resolution, str(i))
                    if not os.path.exists(path):
                        print(f'[ERROR] {path} does not exist')
                        continue

                    if not os.path.exists(os.path.join(path, 'done')):
                        print(f'[ERROR] {path} is not done computing stats')

                    if not os.path.exists(os.path.join(path, 'compare_output.csv')):
                        print(f'[ERROR] {path} is not done comparing')
