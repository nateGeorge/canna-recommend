import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import fnmatch

for root, dirnames, filenames in os.walk('../'):
    for filename in fnmatch.filter(filenames, '*.py'):
            print(filename)
            continue
            print('2to3 -n -w ' + filename)
            subprocess.Popen('autopep8 -n -w ' +
                             filename, shell=True, cwd=root)
