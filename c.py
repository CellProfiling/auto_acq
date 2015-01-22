import sys
import getopt
import subprocess
import re
import time
from itertools import  combinations
from collections import OrderedDict
from control_class import Base
from control_class import Directory
from control_class import File

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
                                                 '63x='
                                                 ])
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
    63x = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-i', '--input'):
            imaging_dir = arg
        elif opt in ('--wdir'):
            working_dir = arg
        elif opt in ('--std'):
            std_well = arg # 'U00V00'
        elif opt in ('--firstgain'):
            first_initialgains_file = arg
        elif opt in ('--secondgain'):
            sec_initialgains_file = arg
        elif opt in ('--finwell'):
            last_well = arg # 'U00V00'
        elif opt in ('--finfield'):
            last_field = arg # 'X00Y00'
        elif opt in ('--63x'):
            63x = arg # True

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

def camstart_com(_afjob, _afr, _afs):
    _com = ('/cli:1 /app:matrix /cmd:startcamscan /runtime:36000'
            ' /repeattime:36000 /afj:'+_afjob+' /afr:'+_afr+' /afs:'+_afs)
    return _com

def gain_com(_job, _pmt, _gain):
    _com = ('/cli:1 /app:matrix /cmd:adjust /tar:pmt /num:'+_pmt+
            ' /exp:'+_job+' /prop:gain /value:'+_gain
            )
    return _com

def get_wfx(_compartment):
    return str(int(re.sub(r'\D', '', re.sub('--.\d\d', '', _compartment)))+1)

def get_wfy(_compartment):
    return str(int(re.sub(r'\D', '', re.sub('.\d\d--', '', _compartment)))+1)

def enable_com(_well, _field):
    wellx = get_wfx(_well)
    welly = get_wfy(_well)
    fieldx = get_wfx(_field)
    fieldy = get_wfy(_field)
    _com = ('/cli:1 /app:matrix /cmd:enable /slide:0 /wellx:'+wellx+
            ' /welly:'+welly+' /fieldx:'+fieldx+' /fieldy:'+fieldy+
            ' /value:true')
    return _com

def cam_com(_job, _well, _field):
    wellx = get_wfx(_well)
    welly = get_wfy(_well)
    fieldx = get_wfx(_field)
    fieldy = get_wfy(_field)
    _com = ('/cli:1 /app:matrix /cmd:add /tar:camlist /exp:'+_job+
           ' /ext:none /slide:0 /wellx:'+_wellx+' /welly:'+_welly+
           ' /fieldx:'+fieldx+' /fieldy:'+fieldy+' /dxpos:0 /dypos:0'
           )
    return _com

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
    """Creat a dict from a list of dicts"""
    output = {}
    for i in input_list:
        output[i[key]] = i[value]
    return output

def round_values(input_dict):
    """Round values taken from a dict. Return a list.
    Replace the values in the old dict as well"""
    output = []
    for k, v in input_dict.iteritems():
        v = int(round(int(v), -1))
        input_dict[k] = v
        output.append(v)
    return output

first_r_script = working_dir+'gain.r'
sec_r_script = working_dir+'gain_change_objectives.r'
path_to_fiji = '/opt/Fiji/ImageJ-linux64'
imagej_macro = working_dir+'do_max_proj_and_calc_histo_arg.ijm'
# Check job names
10x_af_job = 'Job1'
40x_af_job = 'Job2'
40_afr = '105'
40x_afs = '106'
63x_af_job = 'Job3'
10x_g_job = 'Job4'
40x_g_job = 'Job5'
63x_g_job = 'Job6'
40x_job1 = 'Job7'
40x_job2 = 'Job8'
40x_job3 = 'Job9'
40x_pattern = 'Pattern1'
63x_job = ['Job10', 'Job11', 'Job12', 'Job13', 'Job14', 'Job15',
            'Job16', 'Job17', 'Job18', 'Job19', 'Job20', 'Job21'] 
63x_pattern = ['Pattern2', 'Pattern3', 'Pattern4', 'Pattern5'] 
stage1 = True
stage2 = True
stage3 = True
if 63x:
    stage2 = False
    stage3 = False
    stage4 = True
# Check this command and change to make it work
stage2_com = (com_gen(40x_g_job, std_well, 'X00--Y00')+'\n'+
              com_gen(40x_g_job, std_well, 'X01--Y01'))
stage2_end = 'X01--Y01'
start_com = '/cli:1 /app:matrix /cmd:startscan'
stop_com = '/cli:1 /app:matrix /cmd:stopscan'
im_dir = Directory(imaging_dir)
while stage1:
    im_paths = im_dir.get_all_files('*.tif')
    fin_well_paths = []
    for im_path in im_paths:
        image = File(im_path)
        obj_serial = image.serial_no()
        field = Directory(image.get_dir())
        well_path = field.get_dir()
        well = Directory(well_path)
        if well.get_name('U\d\d--V\d\d') == std_well and stage2:
            # Add 40x gain scan in std well to CAM list.
            srv_output = call_server(stage2_com, stage2_end, working_dir)
            camstart = camstart_com(40x_af_job, 40x_afr, 40x_afs)
            # Start CAM scan.
            srv_output = call_server(camstart, stage2_end, working_dir)
            stage2 = False
        # Check serial of 10x objective
        # Find sec_std_path.
        elif (well.get_name('U\d\d--V\d\d') == std_well and
              obj_serial != '11506505'):
            sec_std_path = well_path
        if (len(well.get_all_files('*.tif')) == 66 &
            len(well.get_all_files('*.csv')) == 0):
            fin_well_paths.append(well_path)
            if (well.get_name('U\d\d--V\d\d') == last_well and
                field.get_name('X\d\d--Y\d\d') == last_field):
                stage1 = False
    fin_well_paths = sorted(set(fin_well_paths))
    for well_path in fin_well_paths:
        imagej_output = call_imagej(path_to_fiji, imagej_macro, well_path)
    time.sleep(5)

# Find the top 'slide--S00' directory.
searching = True
search_dir = im_dir
while searching:
    child_paths = search_dir.get_children()
    for p in child_paths:
        search_dir = Directory(p)
        if search_dir.get_name('slide--S\d\d') == 'slide--S00':
            plate_base_path = p
csv_dir = Directory(plate_base_path)
# Get all csv files in top 'slide--S00' directory.
csv_paths = csv_dir.get_all_files('*.csv')
# Get all well names corresponding to all csv files and find first_std_path.
fin_wells = []
for p in csv_paths:
    csv = File(p)
    well = Directory(Directory(csv.get_dir()).get_dir())
    fin_wells.append(well.get_name('U\d\d--V\d\d'))
    if well.get_name('U\d\d--V\d\d') == std_well:
        first_std_path = well.path
first_std_dir = Directory(first_std_path)
sec_std_dir = Directory(sec_std_path)
# Get all csv files in first standard directory.
first_std_csv_paths = first_std_dir.get_all_files('*.csv')
# Get all csv files in second standard directory.
sec_std_csv_paths = sec_std_dir.get_all_files('*.csv')
# Get the filebases from the csv paths.
filebases = cut_path(csv_paths, 'C\d\d.+$')
first_std_fbs = cut_path(first_std_csv_paths, 'C\d\d.+$')
sec_std_fbs = cut_path(sec_std_csv_paths, 'C\d\d.+$')
# Get a unique set of filebases from the csv paths.
filebases = sorted(set(filebases))
first_std_fbs = sorted(set(first_std_fbs))
sec_std_fbs = sorted(set(sec_std_fbs))
# Get a unique set of names of the experiment wells.
fin_wells = sorted(set(fin_wells))
# Lists to store dicts with gain values.
first_gain_dicts = []
sec_gain_dicts = []

# For all experiment wells run R script
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
green = create_dict(sec_gain_dicts, "well", "green")
blue = create_dict(sec_gain_dicts, "well", "blue")
yellow = create_dict(sec_gain_dicts, "well", "yellow")
red = create_dict(sec_gain_dicts, "well", "red")

# Round gain values to multiples of 10
green_list = round_values(green)
blue_list = round_values(blue)
yellow_list = round_values(yellow)
red_list = round_values(red)

# Find the unique set of gain values per channel for whole plate
green_unique = sorted(set(green_list))
blue_unique = sorted(set(blue_list))
yellow_unique = sorted(set(yellow_list))
red_unique = sorted(set(red_list))
# Lists for storing command strings.
stage_com_list = []
stage_end_list = []
green_g_com_list = []
blue_g_com_list = []
yellow_g_com_list = []
red_g_com_list = []
odd_even = 0
well_dict = OrderedDict()
if stage3:
    # Fix this: The combine operation does not work atm.
    for k1, k2 in combinations(green, 2):
        if (green[k1] == green[k2] & blue[k1] == blue[k2] &
            yellow[k1] == yellow[k2] & red[k1] == red[k2]):
            print(green[k2])
            # Set gain in the four channels.
            green_g_com = gain_com(40x_job1, '1', str(green_val))
            blue_g_com = gain_com(40x_job2, '1', str(blue_val))
            yellow_g_com = gain_com(40x_job2, '2', str(yellow_val))
            red_g_com = gain_com(40x_job3, '2', str(red_val))
            stage3_com = ''
            stage3_end = ''
            for i in range(2):
                for j in range(2):
                    # Enable and add 40x job in k well to CAM list.
                    stage3_com = (stage3_com+
                                  enable_com(k,
                                             'X0'+str(j)+
                                             '--Y0'+str(i)
                                             )+
                                  '\n'+
                                  cam_com(40x_pattern,
                                          k,
                                          'X0'+str(j)+'--Y0'+str(i)
                                          )+
                                  '\n')
            stage3_end = k+'.+X01--Y01'
            #testing
            print(k+
                  ' green: '+str(green_val)+
                  ' blue: '+str(blue_val)+
                  ' yellow: '+str(yellow_val)+
                  ' red: '+str(red_val))
            green[k] = -1
            blue[k] = -1
            yellow[k] = -1
            red[k] = -1
        # Remove the last line, should be empty, of a command string.
        stage3_com = stage3_com[:stage3_com.rfind('\n')]
        # Store the commands in lists.
        green_g_com_list.append(green_g_com)
        blue_g_com_list.append(blue_g_com)
        yellow_g_com_list.append(yellow_g_com)
        red_g_com_list.append(red_g_com)
        stage_com_list.append(stage3_com)
        stage_end_list.append(stage3_end)
if stage4:
    green_g_com = ''
    blue_g_com = ''
    yellow_g_com = ''
    red_g_com = ''
    stage4_com = ''
    stage4_end = ''
    for well, green_val in green.iteritems():
        wellx = get_wfx(well)
        welly = get_wfy(well)
        well_no = 8*(int(wellx)-1)+int(welly)
        well_dict[well_no] = well
    well_dict = well_dict(sorted(d.items(), key=lambda t: t[0]))
    for well_no, well in well_dict.iteritems():
    # Check if well no 1-4 or 5-8 etc.
        if round((float(well_no)+1)/4) % 2 != odd_even:
            green_g_com = (green_g_com +
                           gain_com(63x_job[well_no*3-3],
                                    '1',
                                    str(green[well]))+
                           '\n')
            blue_g_com = (blue_g_com +
                          gain_com(63x_job[well_no*3-2],
                                   '1',
                                   str(blue[well]))+
                          '\n')
            yellow_g_com = (yellow_g_com +
                            gain_com(63x_job[well_no*3-2],
                                     '2',
                                     str(yellow[well]))+
                            '\n')
            red_g_com = (red_g_com +
                         gain_com(63x_job[well_no*3-1],
                                  '2',
                                  str(red[well]))+
                         '\n')
            for i in range(2):
                for j in range(2):
                    # Enable and add 63x job in well to CAM list.
                    # Fix this: Add coords from file (arg) per well.
                    # Fix this: Only add selected wells from file (arg)
                    stage4_com = (stage4_com+
                                  enable_com(well,
                                             'X0'+str(j)+
                                             '--Y0'+str(i)
                                             )+
                                  '\n'+
                                  cam_com(63x_pattern1,
                                          well,
                                          'X0'+str(j)+'--Y0'+str(i)
                                          )+
                                  '\n')
            stage4_end = well+'.+X01--Y01'
        elif odd_even == 0:
            odd_even = 1
            # Fix this mess of reps!
            # Remove the last line, should be empty, of a command string.
            stage4_com = stage4_com[:stage4_com.rfind('\n')]
            green_g_com = green_g_com[:green_g_com.rfind('\n')]
            blue_g_com = blue_g_com[:blue_g_com.rfind('\n')]
            yellow_g_com = yellow_g_com[:yellow_g_com.rfind('\n')]
            red_g_com = red_g_com[:red_g_com.rfind('\n')]
            green_g_com_list.append(green_g_com)
            blue_g_com_list.append(blue_g_com)
            yellow_g_com_list.append(yellow_g_com)
            red_g_com_list.append(red_g_com)
            stage_com_list.append(stage4_com)
            stage_end_list.append(stage4_end)
            green_g_com = ''
            blue_g_com = ''
            yellow_g_com = ''
            red_g_com = ''
            stage4_com = ''
            stage4_end = ''
        else
            odd_even = 0
            # Remove the last line, should be empty, of a command string.
            stage4_com = stage4_com[:stage4_com.rfind('\n')]
            green_g_com = green_g_com[:green_g_com.rfind('\n')]
            blue_g_com = blue_g_com[:blue_g_com.rfind('\n')]
            yellow_g_com = yellow_g_com[:yellow_g_com.rfind('\n')]
            red_g_com = red_g_com[:red_g_com.rfind('\n')]
            green_g_com_list.append(green_g_com)
            blue_g_com_list.append(blue_g_com)
            yellow_g_com_list.append(yellow_g_com)
            red_g_com_list.append(red_g_com)
            stage_com_list.append(stage4_com)
            stage_end_list.append(stage4_end)
            green_g_com = ''
            blue_g_com = ''
            yellow_g_com = ''
            red_g_com = ''
            stage4_com = ''
            stage4_end = ''
if stage3:
    camstart = camstart_com(40x_af_job, 40x_afr, 40x_afs)
if stage4:
    camstart = camstart_com(63x_af_job, 63x_afr, 63x_afs)
for i,com in enumerate(stage_com_list):
    # Send gain change command to server in the four channels.
    call_server(green_g_com_list[i], green_g_com_list[i], working_dir)
    call_server(blue_g_com_list[i], blue_g_com_list[i], working_dir)
    call_server(yellow_g_com_list[i], yellow_g_com_list[i], working_dir)
    call_server(red_g_com_list[i], red_g_com_list[i], working_dir)
    # Send CAM list to server.
    call_server(com, stage_end_list[i], working_dir)
    # Start scan.
    call_server(start_com, start_com, working_dir)
    time.sleep(3)
    # Start CAM scan.
    call_server(camstart, stage_end_list[i], working_dir)
    # Stop scan
    call_server(stop_com, stop_com, working_dir)
    time.sleep(3)
