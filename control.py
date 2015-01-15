# Call R script for all csv files (wells) and collect output

import getopt
import sys
import fnmatch
import os
import subprocess
import re
import csv
import time

# Change std_dir to be created from std_well, 10x, 40x
# Make different imaging_dir? 10x, 40x etc.

def usage():
    """Usage function to help user start the script"""
    print 'Usage: '+sys.argv[0]+' -i <dir> [option]'

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hi:', ['help',
                                                 'input=',
                                                 'wdir=',
                                                 'standard=',
                                                 'firstgain=',
                                                 'secondgain=',
                                                 'finwell=',
                                                 'finfield='
                                                 ])
    if not opts:
        print 'No options supplied'
        usage()
    except getopt.GetoptError,e:
        print e
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        elif opt in ('-i', '--input'):
            imaging_dir = arg
        elif opt in ('--wdir'):
            working_dir = arg
        elif opt in ('--standard'):
            std_well = arg #U00V00
        elif opt in ('--firstgain'):
            first_initialgains_file = arg
        elif opt in ('--secondgain'):
            sec_initialgains_file = arg
        elif opt in ('--finwell'):
            last_well = arg #U00V00
        elif opt in ('--finfield'):
            last_field = arg #X00Y00

#working_dir = sys.argv[1]
#imaging_dir = sys.argv[2]
#first_std_dir = sys.argv[3]
#sec_std_dir = sys.argv[4]
#first_initialgains_file = sys.argv[5]
#sec_initialgains_file = sys.argv[6]
#last_well = sys.argv[7] #U00V00
#last_field = sys.argv[8] #X00Y00
first_r_script = working_dir+"gain.r"
sec_r_script = working_dir+"gain_change_objectives.r"
#sec_std_dir = 

path_to_fiji = "/opt/Fiji/ImageJ-linux64"
imagej_macro = working_dir+"do_max_proj_and_calc_histo_arg.ijm"

if __name__ =='__main__':
    main(sys.argv[1:])

def search_files(file_list, rootdir, _match_string):
    """Search for files matching regex and return a list of files.

    Arguments:
    file_list -- list to return
    rootdir -- path to search
    _match_string -- regex to match
    """
    for root, dirnames, filenames in os.walk(rootdir):
        for filename in fnmatch.filter(filenames, _match_string):
            file_list.append(os.path.join(root, filename))
    return file_list

def strip_fun(files, filebases, _wells, _fields, _match_string):
    """Remove the end, matching a regex, of filenames and get the file well.

    Arguments:
    files -- list of files to process
    filebases -- list of processed files
    _wells -- list of wells from the processed files
    _match_string -- regex to match
    """
    for f in files:
        #print(re.sub('C\d\d.+$', '', f))
        filebases.append(re.sub(_match_string, '', f))
        wellmatch = re.search('U\d\d--V\d\d', f)
        fieldmatch = re.search('X\d\d--Y\d\d', f)
        if wellmatch & fieldmatch:                      
            #print('found', wellmatch.group())
            _wells.append(wellmatch.group())
            _fields.append(fieldmatch.group())
        else:
            print 'did not find'
    return

def parent_dir(p):
    """Return parent directory of p"""
    return os.path.abspath(os.path.join(p, os.pardir))

stage1 = True

while stage1:
    images = []
    image_bases = []
    wells = []
    fields = []
    images = search_files(images, imaging_dir, "*.tif")
    strip_fun(images, image_bases, wells, fields, 'C\d\d.+$')
    well_paths = []
    for i in range(len(images)):
        d = parent_dir(parent_dir(images[i]))
        well = wells[i]
        field = fields[i]
        if well == std_well:
            first_std_dir = d
        if well == last_well && field == last_field:
            stage1 = False
        well_images = []
        well_images = search_files(well_images, d, "*.tif")
        csv_list = []
        csv_list = search_files(csv_list, d, "*.csv")
        if len(well_images) == 66 & len(csv_list) == 0:
            well_paths.append(d)
    well_paths = sorted(list(set(well_paths)))
    for well in well_paths:
        imagej_output = subprocess.check_output([path_to_fiji,
                                                 "--headless",
                                                 "-macro",
                                                 imagej_macro,
                                                 well
                                                 ])
    time.sleep(5)

first_files = []
first_files = search_files(first_files, imaging_dir, "*.csv")

first_std_files = []
sec_std_files = []
first_std_files = search_files(first_std_files, first_std_dir, "*.csv")
sec_std_files = search_files(sec_std_files, sec_std_dir, "*.csv")

first_filebases = []
wells = []
fields = []
first_std_filebases = []
sec_std_filebases = []
garbage_wells = []

strip_fun(first_files, first_filebases, wells, fields, 'C\d\d.+$')
strip_fun(first_std_files, first_std_filebases, garbage_wells, fields, 'C\d\d.+$')
strip_fun(sec_std_files, sec_std_filebases, garbage_wells, fields, 'C\d\d.+$')

first_filebases = sorted(list(set(first_filebases)))
wells = sorted(list(set(wells)))
first_std_filebases = sorted(list(set(first_std_filebases)))
sec_std_filebases = sorted(list(set(sec_std_filebases)))

first_gain_dicts = []
sec_gain_dicts = []

def process_output(dict_list, well_list, i, output):
    dict_list.append({"well": well_list[i],
                      "green": output.split()[0],
                      "blue": output.split()[1],
                      "yellow": output.split()[2],
                      "red": output.split()[3]
                      })
    return dict_list

# for all wells run R script
for i in range(len(first_filebases)):
    print(first_filebases[i])
    print(wells[i])
    # Run with "Rscript path/to/script/gain.r path/to/working/dir/
    # path/to/histogram-csv-filebase path/to/initialgains/csv-file"
    # from linux command line.
    r_output = subprocess.check_output(["Rscript",
                                        first_r_script,
                                        imaging_dir,
                                        first_filebases[i],
                                        first_initialgains_file
                                        ])

    first_gain_dicts = process_output(first_gain_dicts, wells, i, r_output)

    input_gains = (""+r_output.split()[0]+" "+r_output.split()[1]+" "+
                    r_output.split()[2]+" "+r_output.split()[3]+"")
    r_output = subprocess.check_output(["Rscript",
                                        sec_r_script,
                                        first_std_dir,
                                        first_std_filebases[0],
                                        first_initialgains_file,
                                        input_gains,
                                        sec_std_dir,
                                        sec_std_filebases[0],
                                        sec_initialgains_file
                                        ])
    # testing
    print(r_output)
    
    sec_gain_dicts = process_output(sec_gain_dicts, wells, i, r_output)

def write_csv(path, dict_list):
    with open(path, 'wb') as f:
        keys = ["well", "green", "blue", "yellow", "red"]
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(dict_list)

write_csv(working_dir+"first_output_gains.csv", first_gain_dicts)
write_csv(working_dir+"sec_output_gains.csv", sec_gain_dicts)
