"""
cleans up python, javascript, html, and css files

uses autopep8 for python; js-beautify for js, html, and css files
"""

import subprocess
import fnmatch
import os
import re
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

cwd = os.path.dirname(os.path.realpath(__file__))
ignore_res = ['.*node_modules.*',
              '.*plugins.*',
              '.*platforms.*',
              '.*jquery_mobile.*']

# clean python, js, html, and css files
filetypes = ['py', 'js', 'html', 'css']
for f in filetypes:
    for root, dirnames, filenames in os.walk('../'):
        for filename in fnmatch.filter(filenames, '*.' + f):
            if f == 'py':
                print('autopep8 --in-place ' + filename)
                subprocess.Popen('autopep8 --in-place ' +
                                 filename, shell=True, cwd=root)
            else:
                print('js-beautify ' + filename + ' --type "' + f + '" -o ' + filename)
                cont = False
                for i in ignore_res:
                    if re.search(i, root) is not None:
                        cont = True
                if re.search('.*\.min.*', filename) is not None:
                    cont = True
                if cont:
                    print('skipping')
                    continue
                print(root)
                subprocess.Popen('js-beautify ' + filename + ' --type "' +
                                 f + '" -o ' + filename, shell=True, cwd=root)
