# Call R script for all csv files (wells) and collect output

import fnmatch
import os
import sys
import subprocess
import re
import csv

working_dir = sys.argv[1]
first_std_working_dir = sys.argv[2]
sec_std_working_dir = sys.argv[3]
first_r_script = "/home/martin/Dev/auto_acq/gain.r"
sec_r_script = "/home/martin/Dev/auto_acq/gain_change_objectives.r"
first_initialgains_file = "/home/martin/Dev/auto_acq/gain.csv"
sec_initialgains_file = "/home/martin/Dev/auto_acq/gain2.csv"

def search_files(file_list, rootdir, _match_string):
    for root, dirnames, filenames in os.walk(rootdir):
        for filename in fnmatch.filter(filenames, _match_string):
            file_list.append(os.path.join(root, filename))
    return file_list

first_files = []
first_files = search_files(first_files, working_dir, "*.csv")

first_std_files = []
sec_std_files = []
first_std_files = search_files(first_std_files, first_std_working_dir, "*.csv")
sec_std_files = search_files(sec_std_files, sec_std_working_dir, "*.csv")

first_filebases = []
wells = []
first_std_filebases = []
sec_std_filebases = []
garbage_wells = []

def strip_fun(files, filebases, _wells):
    for f in files:
        print(re.sub('C\d\d.+$', '', f))
        filebases.append(re.sub('C\d\d.+$', '', f))
        wellmatch = re.search('U\d\d--V\d\d--', f)

        if wellmatch:                      
            print('found', wellmatch.group())
            _wells.append(wellmatch.group())

        else:
            print 'did not find'
    return

strip_fun(first_files, first_filebases, wells)
strip_fun(first_std_files, first_std_filebases, garbage_wells)
strip_fun(sec_std_files, sec_std_filebases, garbage_wells)
first_filebases = list(set(first_filebases))
wells = list(set(wells))
first_std_filebases = list(set(first_std_filebases))
sec_std_filebases = list(set(sec_std_filebases))

first_gain_dicts = []
sec_gain_dicts = []

def process_output(dict_list, well_list, i, output):
    dict_list.append({ "well": well_list[i], "green": output.split()[0] ,
        "blue": output.split()[1] , "yellow": output.split()[2] ,
        "red": output.split()[3]})
    return dict_list

# for all wells run R script
for i in range(len(first_filebases)):
    print(first_filebases[i])
    print(wells[i])
    # Run with "Rscript path/to/script/gain.r path/to/working/dir/
    # path/to/histogram-csv-filebase path/to/initialgains/csv-file"
    # from linux command line.
    r_output = subprocess.check_output(["Rscript", first_r_script,
            working_dir, first_filebases[i], first_initialgains_file])

    first_gain_dicts = process_output(first_gain_dicts, wells, i, r_output)
    # FIX INPUT_GAINS!!!
    input_gains = "\"c("+r_output.split()[0]+","+r_output.split()[1]+","+r_output.split()[2]+","+r_output.split()[3]+")\""
    r_output = subprocess.check_output(["Rscript", sec_r_script,
            first_std_working_dir, first_std_filebases[0],
            first_initialgains_file, input_gains, sec_std_working_dir,
            sec_std_filebases[0], sec_initialgains_file])
    
    sec_gain_dicts = process_output(sec_gain_dicts, wells, i, r_output)

def write_csv(path, dict_list):
    with open(path, 'wb') as f:
        w = csv.DictWriter(f, dict_list.keys())
        w.writeheader()
        w.writerows(dict_list)

write_csv('/home/martin/Skrivbord/first_output_gains.csv', first_gain_dicts)
write_csv('/home/martin/Skrivbord/sec_output_gains.csv', sec_gain_dicts)
