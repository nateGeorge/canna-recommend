import os
import sys
import fnmatch
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
for root, dirnames, filenames in os.walk('../'):
    for filename in fnmatch.filter(filenames, '*.py'):
            print(('2to3 -n -w ' + filename))
            subprocess.Popen('2to3 -n -w ' +
                             filename, shell=True, cwd=root)
