import sys
import os
import getopt
import subprocess
import re
import time
import csv
from lxml import etree
import numpy
from scipy.misc import imread, imsave
from scipy.ndimage.measurements import histogram
from itertools import  combinations
from itertools import groupby
from collections import OrderedDict
from collections import defaultdict
from control_class import Base
from control_class import Directory
from control_class import File
from socket_client import Client

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
    --coords=<file>             : set 63x coordinates file
    --host=<ip>                 : set host ip address""")

def camstart_com(_afjob, _afr, _afs):
    """Returns a cam command to start the cam scan with selected AF job
    and AF settings."""
    
    _com = ('/cli:1 /app:matrix /cmd:startcamscan /runtime:36000'
            ' /repeattime:36000 /afj:'+_afjob+' /afr:'+_afr+' /afs:'+_afs)
    return _com

def gain_com(_job, _pmt, _gain):
    """Returns a cam command for changing the pmt gain in a job."""
    
    _com = ('/cli:1 /app:matrix /cmd:adjust /tar:pmt /num:'+_pmt+
            ' /exp:'+_job+' /prop:gain /value:'+_gain
            )
    return _com

def get_wfx(_compartment):
    """Returns a string representing the well or field X coordinate."""
    
    return str(int(re.sub(r'\D', '', re.sub('--.\d\d', '', _compartment)))+1)

def get_wfy(_compartment):
    """Returns a string representing the well or field Y coordinate."""
    
    return str(int(re.sub(r'\D', '', re.sub('.\d\d--', '', _compartment)))+1)

def enable_com(_well, _field, enable):
    """Returns a cam command to enable a field in a well."""
    
    wellx = get_wfx(_well)
    welly = get_wfy(_well)
    fieldx = get_wfx(_field)
    fieldy = get_wfy(_field)
    _com = ('/cli:1 /app:matrix /cmd:enable /slide:0 /wellx:'+wellx+
            ' /welly:'+welly+' /fieldx:'+fieldx+' /fieldy:'+fieldy+
            ' /value:'+enable)
    return _com

def cam_com(_job, _well, _field, _dx, _dy):
    """Returns a cam command to add a field to the cam list."""
    
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

def process_output(_well, output, dl):
    """Function to process output from the R scripts."""
    
    dl.append({'well': _well,
              'green': output.split()[0],
              'blue': output.split()[1],
              'yellow': output.split()[2],
              'red': output.split()[3]
              })
    return dl

def write_csv(path, dict_list, keys):
    """Function to write a list of dicts as a csv file."""
    
    with open(path, 'wb') as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(dict_list)

def main(argv):
    """Main function"""
    
    try:
        opts, args = getopt.getopt(argv, 'hi:', ['help',
                                                 'input=',
                                                 'wdir=',
                                                 'std=',
                                                 'firstgain=',
                                                 'secondgain=',
                                                 'finwell=',
                                                 'finfield=',
                                                 'coords=',
                                                 'host='
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
    host = ''
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
        elif opt in ('--host'):
            host = arg
        else:
            assert False, 'Unhandled option!'

    # Paths
    first_r_script = os.path.normpath(working_dir+'/gain.r')
    sec_r_script = os.path.normpath(working_dir+'/gain_change_objectives.r')
    
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
    
    # Create imaging directory oject
    im_dir = Directory(imaging_dir)

    # Create socket
    sock = Client()
    # Port number
    port = 8895
    # Connect to server
    sock.connect(host, port)
    

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
                    img = File(im_paths[0])
                    field_path = img.get_dir()
                    field = Directory(field_path)
                    well_path = field.get_dir()
                    #testing
                    print(well_path)
                    well = Directory(well_path)
                    if (well.get_name('U\d\d--V\d\d') == std_well and
                        stage2before):
                        print('Stage2')
                        # Add 40x gain scan in std well to CAM list.
                        sock.send(stage2_com)
                        camstart = camstart_com(af_job_40x, afr_40x, afs_40x)
                        # Start CAM scan.
                        sock.send(camstart)
                        stage2before = False
                    # Find sec_std_path.
                    elif (well.get_name('U\d\d--V\d\d') == std_well and
                          'CAM' in well_path):
                        sec_std_path = well_path
                    if ((len(well.get_all_files('*.tif')) == 66) &
                        (len(well.get_all_files('*.csv')) == 0)):
                        fin_well_paths.append(well_path)
                        if (well.get_name('U\d\d--V\d\d') == last_well and
                            field.get_name('X\d\d--Y\d\d') == last_field):
                            if 'CAM' not in well_path:
                                stage1after = True
                        if 'CAM' in well_path:
                            stage2after = True
        except IndexError as e:
            print('No images in this directory... but maybe in the next?' , e)
        fin_well_paths = sorted(set(fin_well_paths))
        print('Making max projections and calculating histograms')
        for well_path in fin_well_paths:
            ptime = time.time()
            well = Directory(well_path)
            well_name = well.get_name('U\d\d--V\d\d')
            img_paths = sorted(well.get_all_files('*.tif'))
            channels = []
            for img_path in img_paths:
                channel = File(img_path).get_name('C\d\d')
                channels.append(channel)
                channels = sorted(set(channels))
            # Do we need to rename finished images?
            for channel in channels:
                images = []
                for img_path in img_paths:
                    if channel == File(img_path).get_name('C\d\d'):
                        images.append(imread(img_path))
                max_img = np.maximum.reduce(images)
                histo = histogram(max_img, 0, 65535, 256)
                rows = []
                for b, count in enumerate(histo):
                    rows.append({'bin': b, 'count': count})
                write_csv(os.path.normpath(well_path+'/maxprojs/'+well_name+
                                           '--'+channel+'.csv'),
                          rows,
                          ['bin', 'count']
                          )
                #imsave(well_path+'/maxprojs/'+well_name+'--'+channel+'.tif',
                #       max_img
                #       )
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

    try:
        sec_std_dir = Directory(sec_std_path)
    except UnboundLocalError as e:
        print('No objective standards found!')
        sys.exit(2)

    csv_dir = Directory(plate_base_path)
    # Get all csv files in top 'slide--S00' directory.
    csv_paths = csv_dir.get_all_files('*.csv')
    # Get all csv files in second standard directory.
    sec_std_csv_paths = sec_std_dir.get_all_files('*.csv')
    # lists to store filebases of csv-files
    filebases = []
    first_std_fbs = []
    sec_std_fbs = []
    # Get all well names corresponding to all csv files under
    # top 'slide--S00' directory, find first_std_path and get csv base names.
    fin_wells = []
    for csv_list in [csv_paths, sec_std_csv_paths]:    
        for p in csv_list:
            csv_file = File(p)
            # Get the filebases from the csv paths.
            filebase = csv_file.cut_path('C\d\d.+$')
            well = Directory(Directory(csv_file.get_dir()).get_dir())
            if csv_list == csv_paths:
                filebases.append(filebase)
                fin_wells.append(well.get_name('U\d\d--V\d\d'))
                if well.get_name('U\d\d--V\d\d') == std_well:
                    first_std_path = well.path
                    first_std_fbs.append(filebase)
            if csv_list == sec_std_csv_paths:
                sec_std_fbs.append(filebase)
    
    # Get a unique set of filebases from the csv paths.
    filebases = sorted(set(filebases))
    first_std_fbs = sorted(set(first_std_fbs))
    sec_std_fbs = sorted(set(sec_std_fbs))
    # Get a unique set of names of the experiment wells.
    fin_wells = sorted(set(fin_wells))

    first_gain_dicts = []
    sec_gain_dicts = []

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
            first_gain_dicts = process_output(well, r_output, first_gain_dicts)
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
        sec_gain_dicts = process_output(well, r_output, sec_gain_dicts)

    write_csv(os.path.normpath(working_dir+'/first_output_gains.csv'),
              first_gain_dicts,
              ['well', 'green', 'blue', 'yellow', 'red'])
    write_csv(os.path.normpath(working_dir+'/sec_output_gains.csv'),
              sec_gain_dicts,
              ['well', 'green', 'blue', 'yellow', 'red'])

    # Lists for storing command strings.
    com_list = []
    end_com_list = []
    cam_end_list = []

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
            channels = [gain,
                        medians['blue'],
                        medians['yellow'],
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
                        end_com = []
                        end_com.append('CAM')
                        end_com.append(well)
                        end_com.append('E03')
                        end_com.append('X0'+str(j)+'--Y0'+str(i))
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
                    end_com = []
                    end_com.append('CAM')
                    end_com.append(well)
                    end_com.append('E03')
                    end_com.append('X0'+str(j)+'--Y0'+str(i))
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
        print(com)
        sock.send(com)
        # Start scan.
        print(start_com)
        sock.send(start_com)
        time.sleep(3)
        # Start CAM scan.
        print(camstart)
        sock.send(camstart)
        sock.recv_timeout(40, end_com_list[i])
        # Stop scan
        print(stop_com)
        sock.send(stop_com)
        time.sleep(3)

if __name__ =='__main__':
    main(sys.argv[1:])
