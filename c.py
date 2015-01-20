# Make different imaging_dir? 10x, 40x etc.
import sys
import getopt
import subprocess
import re
import time
from control_class import Base
from control_class import Directory
from control_class import MyImage

def usage():
    """Usage function to help user start the script"""
    print("""Usage: """+sys.argv[0]+""" -i <dir> [options]
    
    Options and arguments:
    -h, --help                  : show the usage information
    -i <dir>, --input=<dir>     : set imaging directory
    --wdir=<dir>                : set working directory
    --std=<well>                : set standard well
    --firstgain=<gain_file>     : set first initial gains file
    --secondgain=<gain_file>    : set second initial gains file
    --finwell=<well>            : set final well
    --finfield=<field>          : set final field""")

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hi:', ['help',
                                                 'input=',
                                                 'wdir=',
                                                 'std=',
                                                 'firstgain=',
                                                 'secondgain=',
                                                 'finwell=',
                                                 'finfield='
                                                 ])
    #if not opts:
    #    print 'No options supplied'
    #    usage()
    except getopt.GetoptError,e:
        print e
        usage()
        sys.exit(2)
    
    imaging_dir = None
    working_dir = None
    std_well = None
    first_initialgains_file = None
    sec_initialgains_file = None
    last_well = None
    last_field = None
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-i', '--input'):
            imaging_dir = arg
        elif opt in ('--wdir'):
            working_dir = arg
        elif opt in ('--std'):
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
#first_std_path = sys.argv[3]
#sec_std_path = sys.argv[4]
#first_initialgains_file = sys.argv[5]
#sec_initialgains_file = sys.argv[6]
#last_well = sys.argv[7] #U00V00
#last_field = sys.argv[8] #X00Y00

if __name__ =='__main__':
    main(sys.argv[1:])

def call_server(_command, _end_str, _w_dir):
    output = subprocess.check_output(['python',
                                      _w_dir+'socket_client.py',
                                      _command,
                                      _end_str,
                                      ])
    return output

def call_imagej(path_to_fiji, imagej_macro, im_dir):
    output = subprocess.check_output([path_to_fiji,
                                      '--headless',
                                      '-macro',
                                      imagej_macro,
                                      im_dir
                                      ])
    return output

def cut_path(files, regex):
    cut_paths = []
    for f in files:
        cut_paths.append(re.sub(regex, '', f))
    return cut_paths

def process_output(dict_list, _well, output):
    dict_list.append({'well': _well,
                      'green': output.split()[0],
                      'blue': output.split()[1],
                      'yellow': output.split()[2],
                      'red': output.split()[3]
                      })
    return _dict_list

def write_csv(path, dict_list):
    with open(path, 'wb') as f:
        keys = ['well', 'green', 'blue', 'yellow', 'red']
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(dict_list)

def create_dict(input_list, key, value):
    output = {}
    for i in input_list:
        output[i[key]] = i[value]
    return output

first_r_script = working_dir+'gain.r'
sec_r_script = working_dir+'gain_change_objectives.r'
path_to_fiji = '/opt/Fiji/ImageJ-linux64'
imagej_macro = working_dir+'do_max_proj_and_calc_histo_arg.ijm'
stage1 = True
stage2 = True
std_wellx = str(int(re.sub(r'\D', '', re.sub('--V\d\d', '', std_well)))+1)
std_welly = str(int(re.sub(r'\D', '', re.sub('U\d\d--', '', std_well)))+1)
# Check this command and change to make it work
stage2_com = ('/cli:1 /app:matrix /cmd:add /tar:camlist '
              '/exp:Job17 /ext:none /slide:0 /wellx:'+std_wellx+' /welly:'
              +std_welly+' /fieldx:1 /fieldy:1 /dxpos:0 /dypos:0\n'
              '/cli:1 /app:matrix /cmd:add /tar:camlist '
              '/exp:Job17 /ext:none /slide:0 /wellx:'+std_wellx+' /welly:'
              +std_welly+' /fieldx:2 /fieldy:2 /dxpos:0 /dypos:0'
              )
stage2_end = 'X01--Y01'
# Check serial of 10x objective
im_dir = Directory(imaging_dir)
fin_wells = []
while stage1:
    im_paths = im_dir.get_all_files('*.tif')
    fin_well_paths = []
    for im_path in im_paths:
        image = MyImage(im_path)
        obj_serial = image.serial_no()
        field = Directory(image.get_dir())
        well_path = field.get_dir()
        well = Directory(well_path)
        if well.get_name() == std_well and obj_serial == '11506505':
            first_std_path = well_path
            if stage2:
                srv_output = call_server(stage2_com, stage2_end, working_dir)
                stage2 = False
        elif well.get_name() == std_well:
            sec_std_path = well_path
        if well.get_name() == last_well and field.get_name() == last_field:
            stage1 = False
        if (len(well.get_all_files('*.tif')) == 66 &
            len(well.get_all_files('*.csv')) == 0):
            fin_well_paths.append(well_path)
            fin_wells.append(well.get_name())
    fin_well_paths = sorted(list(set(fin_well_paths)))
    for well_path in fin_well_paths:
        imagej_output = call_imagej(path_to_fiji, imagej_macro, well_path)
    time.sleep(5)

csv_paths = im_dir.get_all_files('*.csv')
first_std_dir = Directory(first_std_path)
sec_std_dir = Directory(sec_std_path)
first_std_csv_paths = first_std_dir.get_all_files('*.csv')
sec_std_csv_paths = sec_std_dir.get_all_files('*.csv')
filebases = cut_path(csv_paths, 'C\d\d.+$')
first_std_fbs = cut_path(first_std_csv_paths, 'C\d\d.+$')
sec_std_fbs = cut_path(sec_std_csv_paths, 'C\d\d.+$')
filebases = sorted(list(set(filebases)))
first_std_fbs = sorted(list(set(first_std_fbs)))
sec_std_fbs = sorted(list(set(sec_std_fbs)))
fin_wells = sorted(list(set(fin_wells)))
first_gain_dicts = []
sec_gain_dicts = []

# for all wells run R script
for i in range(len(filebases)):
    well = fin_wells[i]
    print(first_filebases[i])
    print(well)
    r_output = subprocess.check_output(['Rscript',
                                        first_r_script,
                                        imaging_dir,
                                        filebases[i],
                                        first_initialgains_file
                                        ])
    first_gain_dicts = process_output(first_gain_dicts, well, r_output)
    input_gains = (''+r_output.split()[0]+' '+r_output.split()[1]+' '+
                    r_output.split()[2]+' '+r_output.split()[3]+'')
    r_output = subprocess.check_output(['Rscript',
                                        sec_r_script,
                                        first_std_path,
                                        first_std_fbs[0],
                                        first_initialgains_file,
                                        input_gains,
                                        sec_std_path,
                                        sec_std_fbs[0],
                                        sec_initialgains_file
                                        ])
    # testing
    print(r_output)
    sec_gain_dicts = process_output(sec_gain_dicts, well, r_output)

write_csv(working_dir+'first_output_gains.csv', first_gain_dicts)
write_csv(working_dir+'sec_output_gains.csv', sec_gain_dicts)

# Sort gain data into one dict for each channel
green = create_dict(gains, "well", "green")
blue = create_dict(gains, "well", "blue")
yellow = create_dict(gains, "well", "yellow")
red = create_dict(gains, "well", "red")
