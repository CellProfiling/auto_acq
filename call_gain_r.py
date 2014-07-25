# Call R script for all csv files (wells) and collect output

import fnmatch
import os
import sys
import subprocess
import re

rootdir = sys.argv[1]
match_string = sys.argv[2]

files = []
for root, dirnames, filenames in os.walk(rootdir):
    for filename in fnmatch.filter(filenames, match_string):
        files.append(os.path.join(root, filename))

filebases = []
wells = []
for file in files:
    print(re.sub('C\d\d.+$', '', file))
    filebases.append(re.sub('C\d\d.+$', '', file))
    wellmatch = re.search('U\d\d--V\d\d--', file)

    if wellmatch:                      
        print('found', wellmatch.group())
        wells.append(wellmatch.group())

    else:
        print 'did not find'
filebases = list(set(filebases))
wells = list(set(wells))

r_script = "/home/martin/Dev/auto_acq/gain.r"
working_dir = rootdir
initialgains_file = "/home/martin/Dev/auto_acq/gain.csv"

gain_dicts = []

# for all wells run R script
for i in range(len(filebases)):
    print(filebases[i])
    print(wells[i])
    # Run with "Rscript path/to/script/gain.r path/to/working/dir/
    # path/to/histogram-csv-filebase path/to/initialgains/csv-file"
    # from linux command line.
    r_output = subprocess.check_output(["Rscript", r_script, working_dir,
        filebases[i], initialgains_file])

    gain_dicts.append({ "well": wells[i], "green": r_output.split()[0] ,
        "blue": r_output.split()[1] , "yellow": r_output.split()[2] ,
        "red": r_output.split()[3]})
