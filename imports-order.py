import os
import subprocess
import sys

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_files_to_fix(files):
    print(bcolors.FAIL + "Error: following items need to be fixed:" + bcolors.ENDC)
    print('\n'.join(files))

def print_fixed(file):
    print(bcolors.OKGREEN + "Fixed" + bcolors.ENDC + ": " + file)

def get_all_files():
    file_list = []

    for root, dirs, files in os.walk(os.getcwd() + '/src'):
        for file in files:
            if file.endswith(".ts") or file.endswith(".tsx"):
                file_name = os.path.join(root, file)
                file_list.append(file_name)

    return file_list

def get_staged_files():
    proc = subprocess.Popen(['git', 'diff', '--name-only', '--cached'], stdout=subprocess.PIPE)
    staged_files = proc.stdout.readlines()
    staged_files = [f.decode('utf-8') for f in staged_files]
    staged_files = [f.strip() for f in staged_files]
    return staged_files

def find_end_of_import(lines):
    break_point = 0

    for i in range(len(lines)):
        if 'import' not in lines[i] and '\n' == lines[i-1] and '\n' == lines[i-2] and 'import' in lines[i-3]:
            break_point = i
            break

    return break_point

def order_imports(lines):
    everythong_avobe_imports = []
    first = []
    second = []
    third = []
    forth = []

    had_import = False
    
    for line in lines:
        if line.startswith('import'):
            had_import = True

        if not had_import:
            everythong_avobe_imports.append(line)

        if line.startswith('import') and 'from \'..' in line:
            forth.append(line)
        elif line.startswith('import') and 'from \'.' in line:
            third.append(line)
        elif line.startswith('import') and '/' in line and '@' not in line and 'next/' not in line:
            second.append(line)
        elif line.startswith('import'):
            first.append(line)
    
    result = everythong_avobe_imports

    if len(first) > 0:
        result += first
        result += ['\n']

    if (len(second) > 0):
        result += second
        result += ['\n']

    if (len(third) or len(forth)):
        result += third
        result += forth
        result += ['\n']

    if len(result) > 0:
        result += ['\n']

    return result

def check_imports(lines):
    fixed = order_imports(lines)

    return fixed != lines

def process_files(files, fix):
    files = [f.decode('utf-8') for f in files]
    files = [f.strip() for f in files]

    files_needs_fixing = []

    for file in files:
        if not os.path.exists(file):
            # skip if file doesn't exist, it was deleted
            continue

        with open(file, 'r+') as f:
            lines = f.readlines()
            break_point = find_end_of_import(lines)
            imports = lines[:break_point]
            rest_of_file = lines[break_point:]

            needs_fixing = check_imports(imports)

            if not fix and needs_fixing:
                files_needs_fixing.append(file)

            if fix and needs_fixing:
                f.seek(0)

                imports = order_imports(imports)
                f.writelines(imports + rest_of_file)
                f.truncate()
                print_fixed(file)
    
    if not fix and len(files_needs_fixing) > 0:
        print_files_to_fix(files)
        exit(1)

    exit(0)

fix = False
all = False

if '--fix' in sys.argv[1:]:
    fix = True

if '--all' in sys.argv[1:]:
    fix = True

files = []

if all:
    files = get_all_files()
else:
    files = get_staged_files()

process_files(files, fix)
