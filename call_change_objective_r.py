# Call R script for all csv files (wells) and collect output

import fnmatch
import os
import subprocess

rootdir = sys.argv[1]
match = sys.argv[2]

matches = []
for root, dirnames, filenames in os.walk(rootdir):
  for filename in fnmatch.filter(filenames, match):
      matches.append(os.path.join(root, filename))


r_script = "/home/martin/Dev/auto_acq/gain_change_objectives.r"

first_working_dir = "/home/martin/Skrivbord/test/10x/maxprojs/"
first_filebase = "/home/martin/Skrivbord/test/10x/maxprojs/U00--V00--"
first_initialgains_file = "/home/martin/Dev/auto_acq/gain.csv"
sec_working_dir = "/home/martin/Skrivbord/test/63x/maxprojs/"
sec_filebase = "/home/martin/Skrivbord/test/63x/maxprojs/U00--V00--"
sec_initialgains_file = "/home/martin/Dev/auto_acq/gain2.csv"
input_gains = '"c(800,900,700,600)"'

# Run with "Rscript path/to/script/gain.r path/to/working/dir/
# path/to/histogram-csv-filebase path/to/initialgains/csv-file"
# from linux command line.
r_output = subprocess.check_output(["Rscript", r_script, first_working_dir, first_filebase,
            first_initialgains_file, input_gains, sec_working_dir, sec_filebase,
            sec_initialgains_file])

gain_dicts = [
    { "well": well, "green": r_output.split()[0] , "blue": r_output.split()[1] ,
    "yellow": r_output.split()[2] , "red": r_output.split()[3]}
]
