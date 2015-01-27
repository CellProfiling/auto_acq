import sys
import os
import getopt
import subprocess
import re
import time
import csv
from lxml import etree
import numpy
from itertools import  combinations
from itertools import groupby
from collections import OrderedDict
from collections import defaultdict
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
    --finfield=<field>          : set final field
    --coords=<file>             : set 63x coordinates file""")

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

def enable_com(_well, _field, enable):
    wellx = get_wfx(_well)
    welly = get_wfy(_well)
    fieldx = get_wfx(_field)
    fieldy = get_wfy(_field)
    _com = ('/cli:1 /app:matrix /cmd:enable /slide:0 /wellx:'+wellx+
            ' /welly:'+welly+' /fieldx:'+fieldx+' /fieldy:'+fieldy+
            ' /value:'+enable)
    return _com

def cam_com(_job, _well, _field, _dx, _dy):
    _wellx = get_wfx(_well)
    _welly = get_wfy(_well)
    _fieldx = get_wfx(_field)
    _fieldy = get_wfy(_field)
    _com = ('/cli:1 /app:matrix /cmd:add /tar:camlist /exp:'+_job+
            ' /ext:af /slide:0 /wellx:'+_wellx+' /welly:'+_welly+
            ' /fieldx:'+_fieldx+' /fieldy:'+_fieldy+' /dxpos:'+_dx+
            ' /dypos:'+_dy
            )
    return _com

def call_server(_command, _end_str, _w_dir):
    try:
        print('Sending to server...')
        output = subprocess.check_output(['python',
                                          _w_dir+'/socket_client.py',
                                          _command,
                                          _end_str,
                                          ])
    except OSError as e:
        print('Execution failed:', e)
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        print('Subprocess returned a non-zero exit status:', e)
        sys.exit(2)
    else:
        return output

def call_imagej(path_to_fiji, imagej_macro, im_dir):
    try:
        output = subprocess.check_output([path_to_fiji,
                                          '--headless',
                                          '-macro',
                                          imagej_macro,
                                          im_dir
                                          ])
    except OSError as e:
        print('Execution failed:', e)
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        print('Subprocess returned a non-zero exit status:', e)
        sys.exit(2)
    else:
        return output

def cut_path(files, regex):
    cut_paths = []
    for f in files:
        cut_paths.append(re.sub(regex, '', f))
    return cut_paths

def process_output(_well, output):
    dl = []
    dl.append({'well': _well,
              'green': output.split()[0],
              'blue': output.split()[1],
              'yellow': output.split()[2],
              'red': output.split()[3]
              })
    return dl

def write_csv(path, dict_list):
    with open(path, 'wb') as f:
        keys = ['well', 'green', 'blue', 'yellow', 'red']
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(dict_list)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hi:', ['help',
                                                 'input=',
                                                 'wdir=',
                                                 'std=',
                                                 'firstgain=',
                                                 'secondgain=',
                                                 'finwell=',
                                                 'finfield=',
                                                 'coords='
                                                 ])
    except getopt.GetoptError as e:
        print e
        usage()
        sys.exit(2)

    if not opts:
        usage()
        sys.exit(0)

    imaging_dir = ''
    working_dir = os.path.dirname(os.path.abspath(__file__))
    std_well = 'U00--V00'
    first_initialgains_file = os.path.normpath(working_dir+'/10x_gain.csv')
    sec_initialgains_file = os.path.normpath(working_dir+'/40x_gain.csv')
    last_well = 'U00--V00'
    last_field = 'X01--Y01'
    coord_file = None
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-i', '--input'):
            imaging_dir = os.path.normpath(arg)
        elif opt in ('--wdir'):
            working_dir = os.path.normpath(arg)
        elif opt in ('--std'):
            std_well = arg # 'U00--V00'
        elif opt in ('--firstgain'):
            first_initialgains_file = os.path.normpath(arg)
        elif opt in ('--secondgain'):
            sec_initialgains_file = os.path.normpath(arg)
        elif opt in ('--finwell'):
            last_well = arg # 'U00--V00'
        elif opt in ('--finfield'):
            last_field = arg # 'X00--Y00'
        elif opt in ('--coords'):
            coord_file = os.path.normpath(arg) #
        else:
            assert False, 'Unhandled option!'

    first_r_script = os.path.normpath(working_dir+'/gain.r')
    sec_r_script = os.path.normpath(working_dir+'/gain_change_objectives.r')
    path_to_fiji = os.path.normpath('ImageJ-linux64')
    imagej_macro = os.path.normpath(working_dir+
                                    '/do_max_proj_and_calc_histo_arg.ijm')
    # Job names
    af_job_10x = 'af10x'
    af_job_40x = 'af40x'
    afr_40x = '105'
    afs_40x = '106'
    af_job_63x = 'af63x'
    afr_63x = '50'
    afs_63x = '51'
    g_job_10x = 'gain10x'
    g_job_40x = 'gain40x'
    g_job_63x = 'gain63x'
    job_40x = ['job7', 'job8', 'job9']
    pattern_40x = 'pattern2'
    job_63x = ['job10', 'job11', 'job12', 'job13', 'job14', 'job15',
               'job16', 'job17', 'job18', 'job19', 'job20', 'job21']
    pattern_63x = ['pattern3', 'pattern4', 'pattern5', 'pattern6']
    # Booleans to control flow.
    stage1 = True
    stage1after = False
    stage2before = True
    stage2after = False
    stage3 = True
    stage4 = False
    if coord_file:
        stage2before = False
        stage3 = False
        stage4 = True
        coords = defaultdict(list)
        with open(coord_file) as _file:
            reader = csv.DictReader(_file)
            for d in reader:
                for coord in ['dx', 'dy']:
                    coords[d['fov']].append(d[coord])
        
    # 40x gain command in standard well
    stage2_com = ('/cli:1 /app:matrix /cmd:deletelist'+'\n'+
                  cam_com(g_job_40x, std_well, 'X00--Y00', '0', '0')+
                  '\n'+
                  cam_com(g_job_40x, std_well, 'X01--Y01', '0', '0'))
    stage2_end = ''
    start_com = '/cli:1 /app:matrix /cmd:startscan'
    stop_com = '/cli:1 /app:matrix /cmd:stopscan'
    im_dir = Directory(imaging_dir)

    # timeout
    timeout = 300
    # start time
    begin = time.time()

    while stage1:
        #testing
        print('stage1')
        print('Time: '+str(time.time()))
        if ((time.time()-begin) > timeout):
            print('Timeout! No more images to process!')
            break
        print('Searching for images...')
        fin_well_paths = []
        try:
            im_dir_children = im_dir.get_all_children()
            for im_dir_child in im_dir_children:
                child_dir = Directory(im_dir_child)
                im_paths = sorted(child_dir.get_files('*.tif'))
                if im_paths:
                    image = File(im_paths[0])
                    obj_serial = image.serial_no()
                    #testing
                    print(obj_serial)
                    field_path = image.get_dir()
                    field = Directory(field_path)
                    well_path = field.get_dir()
                    #testing
                    print(well_path)
                    well = Directory(well_path)
                    #testing
                    #print(well.get_name('U\d\d--V\d\d'))
                    if well.get_name('U\d\d--V\d\d') == std_well and stage2before:
                        print('Stage2')
                        # Add 40x gain scan in std well to CAM list.
                        print(call_server(stage2_com, '', working_dir))
                        camstart = camstart_com(af_job_40x, afr_40x, afs_40x)
                        # Start CAM scan.
                        print(call_server(camstart, '', working_dir))
                        stage2before = False
                    # Find sec_std_path.
                    elif (well.get_name('U\d\d--V\d\d') == std_well and
                          obj_serial != '11506505'):
                        sec_std_path = well_path
                    #testing
                    #print(len(well.get_all_files('*.tif')))
                    if ((len(well.get_all_files('*.tif')) == 66) &
                        (len(well.get_all_files('*.csv')) == 0)):
                        fin_well_paths.append(well_path)
                        #testing
                        #print(well.get_name('U\d\d--V\d\d'))                    
                        #print(field.get_name('X\d\d--Y\d\d'))
                        if (well.get_name('U\d\d--V\d\d') == last_well and
                            field.get_name('X\d\d--Y\d\d') == last_field):
                            if obj_serial == '11506505':
                                stage1after = True
                        if obj_serial != '11506505':
                            stage2after = True
        except etree.XMLSyntaxError as e:
            print('XML error:', e)
            sys.exit(2)
        except IndexError as e:
            print('No images in this directory... but maybe in the next?' , e)
        fin_well_paths = sorted(set(fin_well_paths))
        for well_path in fin_well_paths:
            ptime = time.time()
            print('Starting ImageJ...')
            print(call_imagej(path_to_fiji, imagej_macro, well_path))
            print(str(time.time()-ptime)+' secs')
            begin = time.time()
        print('Sleeping 5 secs...')
        time.sleep(5)
        if stage1after and stage2after:
            stage1 = False

    # Find the top 'slide--S00' directory.
    searching = True
    search_dir = im_dir
    while searching:
        child_paths = sorted(search_dir.get_children())
        for p in child_paths:
            #testing
            print(p)
            search_dir = Directory(p)
            if search_dir.get_name('slide--S\d\d') == 'slide--S00':
                plate_base_path = p
                searching = False
        search_dir = Directory(child_paths[0])
    csv_dir = Directory(plate_base_path)
    # Get all csv files in top 'slide--S00' directory.
    csv_paths = csv_dir.get_all_files('*.csv')
    # Get all well names corresponding to all csv files and find first_std_path.
    fin_wells = []
    for p in csv_paths:
        csv_file = File(p)
        well = Directory(Directory(csv_file.get_dir()).get_dir())
        fin_wells.append(well.get_name('U\d\d--V\d\d'))
        if well.get_name('U\d\d--V\d\d') == std_well:
            first_std_path = well.path
    try:
        first_std_dir = Directory(first_std_path)
        sec_std_dir = Directory(sec_std_path)
    except UnboundLocalError as e:
        print('No objective standards found!')
        sys.exit(2)
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

    # For all experiment wells run R script
    for i in range(len(filebases)):
        well = fin_wells[i]
        #print(filebases[i])
        print(well)
        try:
            print('Starting R...')
            r_output = subprocess.check_output(['Rscript',
                                                first_r_script,
                                                imaging_dir,
                                                filebases[i],
                                                first_initialgains_file
                                                ])
            first_gain_dicts = process_output(well, r_output)
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
        except OSError as e:
            print('Execution failed:', e)
            sys.exit()
        except subprocess.CalledProcessError as e:
            print('Subprocess returned a non-zero exit status:', e)
            sys.exit()
        # testing
        print(r_output)
        sec_gain_dicts = process_output(well, r_output)

    write_csv(os.path.normpath(working_dir+'/first_output_gains.csv'),
              first_gain_dicts)
    write_csv(os.path.normpath(working_dir+'/sec_output_gains.csv'),
              sec_gain_dicts)

    # Lists for storing command strings.
    com_list = []
    end_com_list = []
    cam_end_list = []

    end_com = ''
    cam_end = ''
    odd_even = 0
    wells = defaultdict()
    gains = defaultdict(list)
    green_sorted = defaultdict(list)
    medians = defaultdict(int)
    com = '/cli:1 /app:matrix /cmd:deletelist'+'\n'
    dx = ''
    dy = ''
    pattern = 0

    for c in ['green', 'blue', 'yellow', 'red']:
        mlist = []
        for d in sec_gain_dicts:
            # Sort gain data into a list dict with well as key and where the
            # value is a list with a gain value for each channel.
            gains[d['well']].append(d[c])
            if c == 'green':
                # Round gain values to multiples of 10 in green channel
                d['green'] = int(round(int(d['green']), -1))
                green_sorted[d['green']].append(d['well'])
                well_no = 8*(int(get_wfx(d['well']))-1)+int(get_wfy(d['well']))
                wells[well_no] = d['well']
            else:
                # Find the median value of all gains in
                # blue, yellow and red channels.
                mlist.append(int(d[c]))
                medians[c] = int(numpy.median(mlist))

    # Fix this mess of reps!
    if stage3:
        print('Stage3')
        camstart = camstart_com(af_job_40x, afr_40x, afs_40x)
        for gain, v in green_sorted.iteritems():
            channels = [gain, medians['blue'], medians['yellow'],
                        medians['red']
                        ]
            # Set gain in the four channels.
            for i,c in enumerate(channels):
                if i < 2:
                    detector = '1'
                    job = job_40x[i]
                if i >= 2:
                    detector = '2'
                    job = job_40x[i-1]
                com = com + gain_com(job, detector, str(c)) + '\n'
                #testing
                print(channels)
            for well in v:
                print(well)
                for i in range(2):
                    for j in range(2):
                        # Enable and add 40x job in well to CAM list.
                        com = (com +
                               enable_com(well,
                                          'X0'+str(j)+'--Y0'+str(i),
                                          'true'
                                          )+
                               '\n'+
                               cam_com(pattern_40x,
                                       well,
                                       'X0'+str(j)+'--Y0'+str(i),
                                       '0',
                                       '0'
                                       )+
                               '\n')
                        cam_end = cam_com(pattern_40x,
                                          well,
                                          'X0'+str(j)+'--Y0'+str(i),
                                          '0',
                                          '0'
                                          )
                        end_com = well+'.+X0'+str(j)+'--Y0'+str(i)
            # Remove the last line, should be empty, of a command string.
            com = com[:com.rfind('\n')]
            # Store the commands in lists.
            com_list.append(com)
            cam_end_list.append(cam_end)
            end_com_list.append(end_com)

    if stage4:
        print('Stage4')
        camstart = camstart_com(af_job_63x, afr_63x, afs_63x)
        wells = OrderedDict(sorted(wells.items(), key=lambda t: t[0]))
        old_well_no = wells.items()[0][0]-1
        for well_no, well in wells.iteritems():
            channels = range(4)
            for i,c in enumerate(channels):
                if i < 2:
                    detector = '1'
                    job = job_63x[i]
                if i >= 2:
                    detector = '2'
                    job = job_63x[i-1]
                com = com + gain_com(job, detector, str(gains[well][i])) + '\n'
            for i in range(2):
                for j in range(2):
                    # Enable and add 63x job in well to CAM list.
                    # Add coords from file (arg) per well.
                    # Only enable selected wells from file (arg)
                    fov = well+'--X0'+str(j)+'--Y0'+str(i)
                    if fov in coords.keys():
                        enable = 'true'
                        dx = coords[fov][0]
                        dy = coords[fov][1]
                    else:
                        enable = 'false'
                    com = (com +
                           enable_com(well, 'X0'+str(j)+'--Y0'+str(i), enable)+
                           '\n'+
                           cam_com(pattern_63x[pattern],
                                   well,
                                   'X0'+str(j)+'--Y0'+str(i),
                                   dx,
                                   dy
                                   )+
                           '\n')
                    cam_end = cam_com(pattern_63x[pattern],
                                      well,
                                      'X0'+str(j)+'--Y0'+str(i),
                                      dx,
                                      dy
                                      )
                    end_com = '.+CAM.+'+well+'.+X0'+str(j)+'--Y0'+str(i)
            old_well_no = well_no
            # Check if well no 1-4 or 5-8 etc and continuous.
            if ((round((float(well_no)+1)/4) % 2 != odd_even) &
                (old_well_no + 1 == well_no)):
                pattern =+ 1
            else:
                if odd_even == 0:
                    odd_even = 1
                else:
                    odd_even = 0
                pattern = 0
            if ((round((float(well_no)+1)/4) % 2 == odd_even) |
                (old_well_no + 1 != well_no) | (well == last_well)):
                # Remove the last line, should be empty, of a command string.
                com = com[:com.rfind('\n')]
                com_list.append(com)
                cam_end_list.append(cam_end)
                end_com_list.append(end_com)
                com = ''

    for i,com in enumerate(com_list):
        # Send gain change command to server in the four channels.
        # Send CAM list to server.
        #cam_end_list[i]
        print(call_server(com, '', working_dir))
        time.sleep(8)
        # Start scan.
        print(call_server(start_com, '', working_dir))
        time.sleep(8)
        # Start CAM scan.
        print(call_server(camstart, end_com_list[i], working_dir))
        time.sleep(8)
        # Stop scan
        print(call_server(stop_com, '', working_dir))
        time.sleep(8)

if __name__ =='__main__':
    main(sys.argv[1:])
