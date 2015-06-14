import sys
import os
import getopt
import subprocess
import re
import time
import csv
import numpy as np
from scipy.ndimage.measurements import histogram
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
    --firstgain=<file>          : set first initial gains file
    --secondgain=<file>         : set second initial gains file
    --finwell=<well>            : set final well
    --finfield=<field>          : set final field
    --coords=<file>             : set 63x coordinates file
    --host=<ip>                 : set host ip address
    --inputgain=<file>          : set second calculated gains file
    --template=<file>           : set template layout file
    --10x                       : set 10x objective as final objective
    --40x                       : set 40x objective as final objective
    --63x                       : set 63x objective as final objective
    --pre63x                    : stop script after gain scanning
    --uvaf                      : use UV laser for AF jobs""")

def camstart_com(_afjob=None, _afr=None, _afs=None):
    """Returns a cam command to start the cam scan with selected AF job
    and AF settings."""

    if _afjob is None:
        afj = ''
    else:
        afj = ' /afj:' + _afjob
    if _afr is None:
        afr = ''
    else:
        afr = ' /afr:' + _afr
    if _afs is None:
        afs = ''
    else:
        afs = ' /afs:' + _afs

    _com = ('/cli:1 /app:matrix /cmd:startcamscan /runtime:36000'
            ' /repeattime:36000' + afj + afr + afs)
    return _com

def gain_com(_job, _pmt, _gain):
    """Returns a cam command for changing the pmt gain in a job."""

    _com = ('/cli:1 /app:matrix /cmd:adjust /tar:pmt /num:' + _pmt +
            ' /exp:' + _job + ' /prop:gain /value:' + _gain
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
    _com = ('/cli:1 /app:matrix /cmd:enable /slide:0 /wellx:' + wellx +
            ' /welly:' + welly + ' /fieldx:' + fieldx + ' /fieldy:' + fieldy +
            ' /value:' + enable)
    return _com

def cam_com(_job, _well, _field, _dx, _dy):
    """Returns a cam command to add a field to the cam list."""

    _wellx = get_wfx(_well)
    _welly = get_wfy(_well)
    _fieldx = get_wfx(_field)
    _fieldy = get_wfy(_field)
    _com = ('/cli:1 /app:matrix /cmd:add /tar:camlist /exp:' + _job +
            ' /ext:none /slide:0 /wellx:' + _wellx + ' /welly:' + _welly +
            ' /fieldx:' + _fieldx + ' /fieldy:' + _fieldy + ' /dxpos:' + _dx +
            ' /dypos:' + _dy
            )
    return _com

def process_output(well, output, dict_list):
    """Function to process output from the R scripts."""
    for c in output.split():
        dict_list[well].append(c)
    return dict_list

def read_csv(path, index, header):
    """Read a csv file and return a defaultdict of lists."""
    dict = defaultdict(list)
    with open(path) as f:
        reader = csv.DictReader(f)
        for d in reader:
            for key in header:
                dict[d[index]].append(d[key])
    return dict

def write_csv(path, dict, header):
    """Function to write a defaultdict of lists as a csv file."""
    with open(path, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for key, value in dict.iteritems():
            writer.writerow([key] + value)

def make_proj(img_list):
    """Function to make a dict of max projections from a list of paths
    to images. Each channel will make one max projection"""
    channels = []
    try:
        print('Making max projections')
        ptime = time.time()
        sorted_images = defaultdict(list)
        max_imgs = {}
        for path in img_list:
            img = File(path)
            channel = img.get_name('C\d\d')
            sorted_images[channel].append(img.read_image())
            max_imgs[channel] = np.maximum.reduce(sorted_images[channel])
        print('Max proj:' + str(time.time()-ptime) + ' secs')
        return max_imgs
    except IndexError as e:
        print('No images to produce max projection.', e)

def get_imgs(path, imdir, job_order, f_job=None, img_save=None, csv_save=None):
    """Function to handle the acquired images, do renaming,
    max projections etc."""
    if f_job is None:
        f_job = 2
    if img_save is None:
        img_save = True
    if csv_save is None:
        csv_save = True
    img_paths = Directory(path).get_all_files('*' + job_order + '*.tif')
    new_paths = []
    metadata_d = {}
    for img_path in img_paths:
        img = File(img_path)
        img_array = img.read_image()
        well = img.get_name('U\d\d--V\d\d')
        job_order = img.get_name('E\d\d')
        job_ord_int = int(re.sub("\D", "", job_order))
        field = img.get_name('X\d\d--Y\d\d')
        z_slice = img.get_name('Z\d\d')
        channel = img.get_name('C\d\d')
        if job_ord_int == f_job:
            new_name = os.path.normpath(os.path.join(path, well + '--' +
                                        field + '--' + z_slice + '--' +
                                        channel + '.ome.tif'))
        elif job_ord_int == f_job + 1 and channel == 'C00':
            new_name = os.path.normpath(os.path.join(path, well + '--' +
                                        field + '--' + z_slice +
                                        '--C01.ome.tif'))
            channel = 'C01'
        elif job_ord_int == f_job + 1 and channel == 'C01':
            new_name = os.path.normpath(os.path.join(path, well + '--' +
                                        field + '--' + z_slice +
                                        '--C02.ome.tif'))
            channel = 'C02'
        elif job_ord_int == f_job + 2:
            new_name = os.path.normpath(os.path.join(path, well + '--' +
                                        field + '--' + z_slice +
                                        '--C03.ome.tif'))
            channel = 'C03'
        else:
            new_name = img_path
        if len(img_array) == 512 or len(img_array) == 2048:
            new_paths.append(new_name)
            metadata_d[well + '--' + field + '--' + channel] = img.meta_data()
        os.rename(img_path, new_name)
    max_projs = make_proj(new_paths)
    new_dir = os.path.normpath(os.path.join(imdir, 'maxprojs'))
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    if img_save:
        print('Saving images')
    if csv_save:
        print('Calculating histograms')
    for channel, proj in max_projs.iteritems():
        if img_save:
            ptime = time.time()
            p = os.path.normpath(os.path.join(new_dir, 'image--' + well + '--' +
                                 field + '--' + channel + '.tif'))
            metadata = metadata_d[well + '--' + field + '--' + channel]
            File(p).save_image(proj, metadata)
            print('Save image:' + str(time.time()-ptime) + ' secs')
        if csv_save:
            ptime = time.time()
            if proj.dtype.name == 'uint8':
                max_int = 255
            if proj.dtype.name == 'uint16':
                max_int = 65535
            histo = histogram(proj, 0, max_int, 256)
            rows = defaultdict(list)
            for b, count in enumerate(histo):
                rows[b].append(count)
            p = os.path.normpath(os.path.join(new_dir, well + '--' + channel +
                                 '.ome.csv'))
            write_csv(p, rows, ['bin', 'count'])
            print('Save csv:' + str(time.time()-ptime) + ' secs')
    return

def get_csvs(path, exp_t, std_w, fbs, first_fbs, sec_fbs, wells, end_63x):
    """Function to find the correct csv files and get their base names."""
    search = Directory(path)
    csvs = sorted(search.get_all_files('*.ome.csv'))
    for csv_path in csvs:
        csv_file = File(csv_path)
        # Get the filebase from the csv path.
        fbase = csv_file.cut_path('C\d\d.+$')
        #  Get the well from the csv path.
        well_name = csv_file.get_name('U\d\d--V\d\d')
        parent_path = csv_file.get_dir()
        well_path = Directory(parent_path).get_dir()
        if end_63x:
            if 'CAM1' in well_path and exp_t in well_path:
                if std_w == well_name:
                    sec_fbs.append(fbase)
            elif 'CAM1' in well_path:
                fbs.append(fbase)
                wells.append(well_name)
                if std_w == well_name:
                    first_fbs.append(fbase)
        else:
            if 'CAM2' in well_path:
                if std_w == well_name:
                    sec_fbs.append(fbase)
            elif 'CAM1' in well_path:
                fbs.append(fbase)
                wells.append(well_name)
                if std_w == well_name:
                    first_fbs.append(fbase)
    return {'wells':wells, 'bases':fbs, 'first':first_fbs, 'sec':sec_fbs}

def parse_reply(reply, root):
    """Function to parse the reply from the server to find the
    correct file path."""
    reply = reply.replace('/relpath:', '')
    paths = reply.split('\\')
    for path in paths:
        root = os.path.join(root, path)
    return root

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
                                                 'host=',
                                                 'inputgain=',
                                                 'template=',
                                                 '10x',
                                                 '40x',
                                                 '63x',
                                                 'pre63x',
                                                 'uvaf'
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
    first_initialgains_file = os.path.normpath(os.path.join(working_dir,
                                                            '10x_gain.csv'))
    sec_initialgains_file = os.path.normpath(os.path.join(working_dir,
                                                          '40x_gain.csv'))
    last_well = 'U00--V00'
    last_field = 'X01--Y01'
    template_file = None
    coord_file = None
    sec_gain_file = None
    host = ''
    end_10x = False
    end_40x = False
    end_63x = False
    pre_63x = False
    first_job = 2
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
        elif opt in ('--inputgain'):
            sec_gain_file = arg
        elif opt in ('--template'):
            template_file = arg
        elif opt in ('--10x'):
            end_10x = True
        elif opt in ('--40x'):
            end_40x = True
        elif opt in ('--63x'):
            end_63x = True
        elif opt in ('--pre63x'):
            pre_63x = True
        elif opt in ('--uvaf'):
            first_job = 1
        else:
            assert False, 'Unhandled option!'

    # Paths
    first_r_script = os.path.normpath(os.path.join(working_dir, 'gain.r'))
    sec_r_script = os.path.normpath(os.path.join(working_dir,
                                                 'gain_change_objectives.r'))

    # Job names
    af_job_10x = 'af10xcam'
    afr_10x = '200'
    afs_10x = '41'
    af_job_40x = 'af40x'
    afr_40x = '105'
    afs_40x = '106'
    af_job_63x = 'af63x'
    afr_63x = '50'
    afs_63x = '51'
    g_job_10x = 'gain10x'
    g_job_40x = 'gain40x'
    g_job_63x = 'gain63x'
    pattern_g_10x = 'pattern7'
    pattern_g_40x = 'pattern8'
    pattern_g_63x = 'pattern9'
    job_10x = ['job22', 'job23', 'job24']
    pattern_10x = 'pattern10'
    job_40x = ['job7', 'job8', 'job9']
    pattern_40x = 'pattern2'
    job_63x = ['job10', 'job11', 'job12', 'job13', 'job14', 'job15',
               'job16', 'job17', 'job18', 'job19', 'job20', 'job21']
    pattern_63x = ['pattern3', 'pattern4', 'pattern5', 'pattern6']
    job_dummy_10x = 'dummy10x'
    pattern_dummy_10x = 'pdummy10x'
    pattern_dummy_40x = 'pdummy40x'

    end_slice = 'Z00'

    stage1_com = '/cli:1 /app:matrix /cmd:deletelist\n'

    # Booleans to control flow.
    stage0 = True
    stage1 = True
    stage1after = False
    stage2before = True
    stage2after = False
    stage3 = True
    stage4 = False
    stage5 = False
    if end_10x:
        end_40x = False
        end_63x = False
    elif end_40x:
        end_10x = False
        end_63x = False
    if coord_file:
        end_63x = True
        coords = read_csv(coord_file, 'fov', ['dxPx', 'dyPx'])
    if end_63x:
        stage1 = False
        stage1after = True
        end_10x = False
        end_40x = False
        stage3 = False
        stage4 = True
        end_slice = 'Z08'
    elif pre_63x:
        stage3 = False
        stage4 = False
    if sec_gain_file:
        stage0 = False
    if template_file:
        template = read_csv(template_file, 'gain_from_well', ['well'])
        last_well = sorted(template.keys())[-1]
        # 10x gain job cam command in selected wells from template file
        for well in sorted(template.keys()):
            for i in range(2):
                stage1_com = (stage1_com +
                              cam_com(pattern_g_10x,
                                      'U0' + str(int(get_wfx(well)) - 1) +
                                        '--V0' + str(int(get_wfy(well)) - 1),
                                      'X0' + str(i) + '--Y0' + str(i),
                                      '0',
                                      '0'
                                      ) +
                              '\n')
    else:
        # 10x gain job cam command in all selected wells
        for u in range(int(get_wfx(last_well))):
            for v in range(int(get_wfy(last_well))):
                for i in range(2):
                    stage1_com = (stage1_com +
                                  cam_com(pattern_g_10x,
                                          'U0' + str(u) + '--V0' + str(v),
                                          'X0' + str(i) + '--Y0' + str(i),
                                          '0',
                                          '0'
                                          ) +
                                  '\n')

    #stage1_com = stage1_com + '/cli:1 /app:matrix /cmd:pausescan\n'

    # 10x gain job cam command in standard well
    stage2_10x = ('/cli:1 /app:matrix /cmd:deletelist\n' +
                  cam_com(pattern_g_10x, std_well, 'X00--Y00', '0', '0') +
                  '\n' +
                  cam_com(pattern_g_10x, std_well, 'X01--Y01', '0', '0'))

    # 40x gain job cam command in standard well
    stage2_40x = ('/cli:1 /app:matrix /cmd:deletelist\n' +
                  cam_com(pattern_g_40x, std_well, 'X00--Y00', '0', '0') +
                  '\n' +
                  cam_com(pattern_g_40x, std_well, 'X01--Y01', '0', '0'))

    # 63x gain job cam command in standard well
    stage2_63x = ('/cli:1 /app:matrix /cmd:deletelist\n' +
                  cam_com(pattern_g_63x, std_well, 'X00--Y00', '0', '0') +
                  '\n' +
                  cam_com(pattern_g_63x, std_well, 'X01--Y01', '0', '0'))

    start_com = '/cli:1 /app:matrix /cmd:startscan\n'
    stop_com = '/cli:1 /app:matrix /cmd:stopscan\n'
    stop_cam_com = '/cli:1 /app:matrix /cmd:stopcamscan\n'

    # Create socket
    sock = Client()
    # Port number
    port = 8895
    # Connect to server
    sock.connect(host, port)

    # timeout
    timeout = 600
    # start time
    begin = time.time()

    # Timestamp part of path of current experiment folder
    exp_time = ''

    # lists for keeping csv file base path names and
    # corresponding well names
    filebases = []
    first_std_fbs = []
    sec_std_fbs = []
    fin_wells = []

    first_gain_dict = defaultdict(list)
    sec_gain_dict = defaultdict(list)

    while stage0:
        print('stage0')
        print('Time: ' + str(time.time()-begin) + ' secs')
        if ((time.time()-begin) > timeout):
            print('Timeout! No more images to process!')
            break
        print('Waiting for images...')
        try:
            if stage1:
                print('Stage1')
                # Add 10x gain scan for wells to CAM list.
                sock.send(stage1_com)
                # Start scan.
                print(start_com)
                sock.send(start_com)
                time.sleep(5)
                cstart = camstart_com()
                # Start CAM scan.
                print(cstart)
                # Start CAM scan.
                sock.send(cstart)
                stage1 = False
            elif end_63x and stage2before:
                print('Stage2')
                # Add 10x gain scan for wells to CAM list.
                sock.send(stage2_63x)
                # Start scan.
                print(start_com)
                sock.send(start_com)
                time.sleep(5)
                cstart = camstart_com()
                # Start CAM scan.
                print(cstart)
                # Start CAM scan.
                sock.send(cstart)
                stage2before = False
            reply = sock.recv_timeout(40, ['image--'])
            for line in reply.splitlines():
                # Parse reply, check well (UV), field (XY).
                # Get well path.
                # Get all image paths in well.
                # Make a max proj per channel and well.
                # Save meta data and image max proj.
                if 'image' in line:
                    root = parse_reply(line, imaging_dir)
                    img = File(root)
                    img_name = img.get_name('image--.*.tif')
                    search = 'experiment--\d\d\d\d_\d\d_\d\d_\d\d_\d\d_\d\d'
                    exp_time = img.get_name(search)
                    print(exp_time)
                    well_name = img.get_name('U\d\d--V\d\d')
                    field_name = img.get_name('X\d\d--Y\d\d')
                    channel = img.get_name('C\d\d')
                    z_slice = img.get_name('Z\d\d')
                    field_path = img.get_dir()
                    well_path = Directory(field_path).get_dir()
                    if (well_name == std_well and stage2before):
                        print('Stage2')
                        time.sleep(3)
                        if end_10x or pre_63x:
                            # Add 10x gain scan in std well to CAM list.
                            sock.send(stage2_10x)
                            cstart = camstart_com()
                        elif end_40x:
                            # Add 40x gain scan in std well to CAM list.
                            sock.send(stage2_40x)
                            cstart = camstart_com()
                        # Start CAM scan.
                        sock.send(cstart)
                        stage2before = False
                    if (field_name == last_field and channel == 'C31' and
                        z_slice == end_slice):
                        if ('CAM2' in well_path or
                            (end_63x and 'CAM1' in well_path and
                             exp_time in well_path)):
                            stage2after = True
                        if ((well_name == last_well) and
                            ('CAM2' not in well_path)):
                            stage1after = True
                        if stage1after and stage2after:
                            stage0 = False
                            print(stop_com)
                            sock.send(stop_com)
                            time.sleep(5)
                        if 'CAM' not in well_path:
                            make_projs = False
                        else:
                            make_projs = True
                        ptime = time.time()
                        if make_projs:
                            get_imgs(well_path,
                                     well_path,
                                     'E02',
                                     img_save=False
                                     )
                            print(str(time.time()-ptime) + ' secs')
                            begin = time.time()
                        # get all CSVs and wells
                        if end_63x:
                            search_dir = imaging_dir
                        else:
                            search_dir = well_path
                        csv_result = get_csvs(search_dir,
                                              exp_time,
                                              std_well,
                                              filebases,
                                              first_std_fbs,
                                              sec_std_fbs,
                                              fin_wells,
                                              end_63x
                                              )
                        filebases = csv_result['bases']
                        first_std_fbs = csv_result['first']
                        sec_std_fbs = csv_result['sec']
                        fin_wells = csv_result['wells']
        except IndexError as e:
            print('No images yet... but maybe later?', e)

        # For all experiment wells imaged so far, run R script
        if filebases and first_std_fbs and sec_std_fbs:
            # Get a unique set of filebases from the csv paths.
            filebases = sorted(set(filebases))
            first_std_fbs = sorted(set(first_std_fbs))
            sec_std_fbs = sorted(set(sec_std_fbs))
            # Get a unique set of names of the experiment wells.
            fin_wells = sorted(set(fin_wells))
            for fbase, well in zip(filebases, fin_wells):
                print(well)
                try:
                    print('Starting R...')
                    r_output = subprocess.check_output(['Rscript',
                                                        first_r_script,
                                                        imaging_dir,
                                                        fbase,
                                                        first_initialgains_file
                                                        ])
                    first_gain_dict = process_output(well,
                                                      r_output,
                                                      first_gain_dict
                                                      )
                    input_gains = r_output
                    r_output = subprocess.check_output(['Rscript',
                                                        sec_r_script,
                                                        imaging_dir,
                                                        first_std_fbs[0],
                                                        first_initialgains_file,
                                                        input_gains,
                                                        imaging_dir,
                                                        sec_std_fbs[0],
                                                        sec_initialgains_file
                                                        ])
                except OSError as e:
                    print('Execution failed:', e)
                    sys.exit()
                except subprocess.CalledProcessError as e:
                    print('Subprocess returned a non-zero exit status:', e)
                    sys.exit()
                print(r_output)
                sec_gain_dict = process_output(well, r_output, sec_gain_dict)
            # empty lists for keeping csv file base path names
            # and corresponding well names
            filebases = []
            fin_wells = []

    if not sec_gain_file:
        header = ['well', 'green', 'blue', 'yellow', 'red']
        csv_files = ['first_output_gains.csv', 'sec_output_gains.csv']
        for name, d in zip(csv_files, [first_gain_dict, sec_gain_dict]):
            write_csv(os.path.normpath(os.path.join(working_dir, name)),
                      d,
                      header
                      )
    else:
        sec_gain_dict = read_csv(sec_gain_file,
                                 'well',
                                 ['green', 'blue', 'yellow', 'red']
                                 )

    # Lists for storing command strings.
    com_list = []
    end_com_list = []
    com = '/cli:1 /app:matrix /cmd:deletelist\n'
    end_com = ['/cli:1 /app:matrix /cmd:deletelist\n']

    wells = defaultdict()
    green_sorted = defaultdict(list)
    medians = defaultdict(int)

    for i, c in enumerate(['green', 'blue', 'yellow', 'red']):
        mlist = []
        for k, v in sec_gain_dict.iteritems():
            # Sort gain data into a list dict with well as key and where the
            # value is a list with a gain value for each channel.
            if c == 'green':
                # Round gain values to multiples of 10 in green channel
                green_val = int(round(int(v[i]), -1))
                if template_file:
                    for well in template[k]:
                        green_sorted[green_val].append(well)
                        well_no = 8*(int(get_wfx(well))-1) + int(get_wfy(well))
                        wells[well_no] = well
                else:
                    green_sorted[green_val].append(k)
                    well_no = 8*(int(get_wfx(k))-1) + int(get_wfy(k))
                    wells[well_no] = k
            else:
                # Find the median value of all gains in
                # blue, yellow and red channels.
                mlist.append(int(v[i]))
                medians[c] = int(np.median(mlist))
    wells = OrderedDict(sorted(wells.items(), key=lambda t: t[0]))

    odd_even = 0
    dx = 0
    dy = 0
    pattern = -1
    start_of_part = False
    fov_is = True
    prev_well = ''
    set_gain = ''
    stage_dict = defaultdict()

    if stage3:
        print('Stage3')
        cstart = camstart_com()
        stage_dict = green_sorted
        pattern = 0
        if end_10x:
            job_list = job_10x
            pattern_list = pattern_10x
        elif end_40x:
            job_list = job_40x
            pattern_list = pattern_40x
        enable = 'true'
    if stage4:
        print('Stage4')
        cstart = camstart_com()
        #channels = range(4)
        stage_dict = wells
        old_well_no = wells.items()[0][0] - 1
        job_list = job_63x
        fov_is = False
    for k, v in stage_dict.iteritems():
        if stage3:
            fov_is = True
            channels = [k,
                        medians['blue'],
                        medians['yellow'],
                        medians['red']
                        ]
        if stage4:
            channels = [sec_gain_dict[v][0],
                        medians['blue'],
                        medians['yellow'],
                        medians['red']
                        ]
            # Check if well no 1-4 or 5-8 etc and continuous.
            if round((float(k)+1) / 4) % 2 == odd_even:
                pattern = 0
                start_of_part = True
                if odd_even == 0:
                    odd_even = 1
                else:
                    odd_even = 0
            elif old_well_no + 1 != k:
                pattern = 0
                start_of_part = True
            else:
                pattern += 1
                start_of_part = False
            pattern_list = pattern_63x[pattern]
            old_well_no = k
        if start_of_part and fov_is:
            # Store the commands in lists, after one well at least.
            com_list.append(com)
            end_com_list.append(end_com)
            com = '/cli:1 /app:matrix /cmd:deletelist\n'
            fov_is = False
        elif start_of_part and not fov_is:
            # reset the com string
            com = '/cli:1 /app:matrix /cmd:deletelist\n'
        for i, c in enumerate(channels):
            set_gain = str(c)
            if stage3:
                start_of_part = True
                fov_is = True
            if i < 2:
                detector = '1'
                job = job_list[i + 3*pattern]
            if i >= 2:
                detector = '2'
                job = job_list[i - 1 + 3*pattern]
            com = com + gain_com(job, detector, set_gain) + '\n'
        for well in v:
            if stage4:
                well = v
            if well != prev_well:
                prev_well = well
                for i in range(2):
                    for j in range(2):
                        if stage4:
                            # Only enable selected wells from file (arg)
                            fov = '{}--X0{}--Y0{}'.format(well, j, i)
                            if coord_file and fov in coords.keys():
                                enable = 'true'
                                dx = coords[fov][0]
                                dy = coords[fov][1]
                                fov_is = True
                            elif end_63x:
                                enable = 'true'
                                fov_is = True
                            else:
                                enable = 'false'
                        if enable == 'true' or stage3:
                            com = (com +
                                   enable_com(well,
                                              'X0{}--Y0{}'.format(j, i),
                                              enable
                                              ) +
                                   '\n' +
                                   # dx dy switched, scan rot -90 degrees
                                   cam_com(pattern_list,
                                           well,
                                           'X0{}--Y0{}'.format(j, i),
                                           str(dy),
                                           str(dx)
                                           ) +
                                   '\n')
                            end_com = ['CAM',
                                       well,
                                       'E0' + str(first_job + 2),
                                       'X0{}--Y0{}'.format(j, i)
                                       ]
    if fov_is:
        # Store the last unstored commands in lists, after one well at least.
        com_list.append(com)
        end_com_list.append(end_com)

    if stage3 or stage4:
        for com, end_com in zip(com_list, end_com_list):
            # Send gain change command to server in the four channels.
            # Send CAM list to server.
            print(com)
            sock.send(com)
            time.sleep(3)
            # Start scan.
            print(start_com)
            sock.send(start_com)
            time.sleep(3)
            # Start CAM scan.
            print(cstart)
            sock.send(cstart)
            time.sleep(3)
            if stage3:
                stage5 = True
                img_saving = False
                #sock.recv_timeout(40, end_com)
            if stage4:
                stage5 = True
                img_saving = True
            while stage5:
                reply = sock.recv_timeout(120, ['image--'])
                for line in reply.splitlines():
                    # parse reply, check well (UV), job-order (E), field (XY),
                    # z slice (Z) and channel (C). Get field path.
                    # Get all image paths in field. Rename images.
                    # Make a max proj per channel and field.
                    # Save meta data and image max proj.
                    if 'image' in line:
                        error = True
                        count = 0
                        while error and count < 2:
                            try:
                                root = parse_reply(line, imaging_dir)
                                img = File(root)
                                img_name = img.get_name('image--.*.tif')
                                print(img_name)
                                job_order = img.get_name('E\d\d')
                                field_path = img.get_dir()
                                get_imgs(field_path,
                                         imaging_dir,
                                         job_order,
                                         f_job=first_job,
                                         img_save=img_saving,
                                         csv_save=False
                                         )
                                error = False
                            except IndexError as e:
                                print('No images yet... but maybe later?' , e)
                                error = False
                            except TypeError as e:
                                error = True
                                count += 1
                                time.sleep(1)
                                print('No images yet... but maybe later?' , e)
                    if all(test in line for test in end_com):
                        stage5 = False
            #time.sleep(3)
            # Stop scan
            print(stop_cam_com)
            sock.send(stop_cam_com)
            time.sleep(3)
            print(stop_com)
            sock.send(stop_com)
            time.sleep(5)

    print('\nExperiment finished!')

if __name__ =='__main__':
    main(sys.argv[1:])
