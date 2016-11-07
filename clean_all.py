import subprocess
import fnmatch
import os

pyfiles = []
for root, dirnames, filenames in os.walk('./'):
    for filename in fnmatch.filter(filenames, '*.py'):
        pyfiles.append(os.path.join(root, filename))
        subprocess.call('autopep8 --in-place' + filename)
