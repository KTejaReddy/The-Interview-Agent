import os, glob
src_path = r't:\The Interview Agent\frontend\src'
hooks = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(src_path, 'hooks', '*.ts'))]
all_files = glob.glob(os.path.join(src_path, '**', '*.ts*'), recursive=True)

unused = []
for h in hooks:
    used = False
    for f in all_files:
        if os.path.basename(f) == f'{h}.ts':
            continue
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            if h in content:
                used = True
                break
    if not used: unused.append(h)
print('Unused hooks:', unused)

