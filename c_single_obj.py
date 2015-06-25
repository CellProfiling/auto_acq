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
    --gainfile=<file>           : set initial gains file
    --finwell=<well>            : set final well
    --finfield=<field>          : set final field
    --coords=<file>             : set 63x coordinates file
    --host=<ip>                 : set host ip address
    --inputgain=<file>          : set second calculated gains file
    --template=<file>           : set template layout file
    --10x                       : set 10x objective as final objective
    --40x                       : set 40x objective as final objective
    --63x                       : set 63x objective as final objective
    --uvaf                      : use UV laser for AF jobs
    --gain                      : stop script after gain scanning""")

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
    dict_list = defaultdict(list)
    with open(path) as f:
        reader = csv.DictReader(f)
        for d in reader:
            for key in header:
                dict_list[d[index]].append(d[key])
    return dict_list

def write_csv(path, d, header):
    """Function to write a defaultdict of lists as a csv file."""
    with open(path, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for key, value in d.iteritems():
            writer.writerow([key] + value)

def make_proj(img_list):
    """Function to make a dict of max projections from a list of paths
    to images. Each channel will make one max projection"""
    channels = []
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
            new_name = os.path.normpath(os.path.join(path, (well + '--' +
                                                            job_order + '--' +
                                                            field + '--' +
                                                            z_slice + '--' +
                                                            channel +
                                                            '.ome.tif'
                                                            )
                                                     )
                                        )
        elif job_ord_int == f_job + 1 and channel == 'C00':
            new_name = os.path.normpath(os.path.join(path, (well + '--' +
                                                            job_order + '--' +
                                                            field + '--' +
                                                            z_slice +
                                                            '--C01.ome.tif'
                                                            )
                                                     )
                                        )
            channel = 'C01'
        elif job_ord_int == f_job + 1 and channel == 'C01':
            new_name = os.path.normpath(os.path.join(path, (well + '--' +
                                                            job_order + '--' +
                                                            field + '--' +
                                                            z_slice +
                                                            '--C02.ome.tif'
                                                            )
                                                     )
                                        )
            channel = 'C02'
        elif job_ord_int == f_job + 2:
            new_name = os.path.normpath(os.path.join(path, (well + '--' +
                                                            job_order + '--' +
                                                            field + '--' +
                                                            z_slice +
                                                            '--C03.ome.tif'
                                                            )
                                                     )
                                        )
            channel = 'C03'
        else:
            new_name = img_path
        if not (len(img_array) == 16 or len(img_array) == 256):
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
                                 field + '--' + channel + '.ome.tif'))
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

def get_csvs(path, fbs, wells):
    """Function to find the correct csv files and get their base names."""
    search = Directory(path)
    csvs = sorted(search.get_all_files('*.ome.csv'))
    for csv_path in csvs:
        csv_file = File(csv_path)
        # Get the filebase from the csv path.
        fbase = csv_file.cut_path('C\d\d.+$')
        #  Get the well from the csv path.
        well_name = csv_file.get_name('U\d\d--V\d\d')
        fbs.append(fbase)
        wells.append(well_name)
    return {'wells':wells, 'bases':fbs}

def parse_reply(reply, root):
    """Function to parse the reply from the server to find the
    correct file path."""
    reply = reply.replace('/relpath:', '')
    paths = reply.split('\\')
    for path in paths:
        root = os.path.join(root, path)
    return root

def set_gain(com, channels, job_list):
    for i, c in enumerate(channels):
        gain = str(c)
        if i < 2:
            detector = '1'
            job = job_list[i]
        if i >= 2:
            detector = '2'
            job = job_list[i - 1]
        com = com + gain_com(job, detector, gain) + '\n'
    return com

def gen_cam_com(com, pattern, well, fieldx, fieldy, enable, dx, dy):
    com = (com +
           #enable_com(well,
            #          'X0{}--Y0{}'.format(fieldx, fieldy),
            #          enable
            #          ) +
           #'\n' +
           # dx dy switched, scan rot -90 degrees
           cam_com(pattern,
                   well,
                   'X0{}--Y0{}'.format(fieldx, fieldy),
                   str(dy),
                   str(dx)
                   ) +
           '\n')
    return com

def gen_com(gain_dict,
            template,
            job_list,
            pattern,
            first_job,
            coords=None
            ):
    parsed = parse_gain(gain_dict, template=template)
    green_sorted = parsed['green']
    medians = parsed['medians']
    dx = 0
    dy = 0
    # Lists for storing command strings.
    com_list = []
    end_com_list = []
    for gain, wells in green_sorted.iteritems():
        com = ''
        end_com = []
        channels = [gain,
                    medians['blue'],
                    medians['yellow'],
                    medians['red']
                    ]
        com = set_gain(com, channels, job_list)
        if coords is None:
            coords = {}
        for well in sorted(wells):
            for i in range(2):
                for j in range(2):
                    # Only enable selected wells from file (arg)
                    fov = '{}--X0{}--Y0{}'.format(well, j, i)
                    if fov in coords.keys():
                        enable = 'true'
                        dx = coords[fov][0]
                        dy = coords[fov][1]
                        fov_is = True
                    elif not coords:
                        enable = 'true'
                        fov_is = True
                    else:
                        enable = 'false'
                        fov_is = False
                    if fov_is:
                        com = gen_cam_com(com,
                                          pattern,
                                          well,
                                          j,
                                          i,
                                          enable,
                                          dx,
                                          dy
                                          )
                        end_com = ['CAM',
                                   well,
                                   'E0' + str(first_job + 2),
                                   'X0{}--Y0{}'.format(j, i)
                                   ]
        # Store the commands in lists.
        com_list.append(com)
        end_com_list.append(end_com)
    return {'com': com_list, 'end_com': end_com_list}

def run_r(filebases,
          fin_wells,
          r_script,
          imaging_dir,
          initialgains_file,
          gain_dict
          ):
    # Get a unique set of filebases from the csv paths.
    filebases = sorted(set(filebases))
    # Get a unique set of names of the experiment wells.
    fin_wells = sorted(set(fin_wells))
    for fbase, well in zip(filebases, fin_wells):
        print(well)
        try:
            print('Starting R...')
            r_output = subprocess.check_output(['Rscript',
                                                r_script,
                                                imaging_dir,
                                                fbase,
                                                initialgains_file
                                                ])
            gain_dict = process_output(well, r_output, gain_dict)
        except OSError as e:
            print('Execution failed:', e)
            sys.exit()
        except subprocess.CalledProcessError as e:
            print('Subprocess returned a non-zero exit status:', e)
            sys.exit()
        print(r_output)
    return gain_dict

def get_gain(line,
             imaging_dir,
             last_field,
             end_63x,
             sock,
             stop_com,
             r_script,
             initialgains_file,
             gain_dict
             ):
    # empty lists for keeping csv file base path names
    # and corresponding well names
    filebases = []
    fin_wells = []
    # Parse reply, check well (UV), field (XY).
    # Get well path.
    # Get all image paths in well.
    # Make a max proj per channel and well.
    # Save meta data and image max proj.
    if 'image' in line:
        root = parse_reply(line, imaging_dir)
        img = File(root)
        img_name = img.get_name('image--.*.tif')
        field_name = img.get_name('X\d\d--Y\d\d')
        channel = img.get_name('C\d\d')
        field_path = img.get_dir()
        well_path = Directory(field_path).get_dir()
        if (field_name == last_field and channel == 'C31'):
            if end_63x:
                sock.send(stop_com)
            ptime = time.time()
            get_imgs(well_path,
                     well_path,
                     'E02',
                     img_save=False
                     )
            print(str(time.time()-ptime) + ' secs')
            # get all CSVs and wells
            csv_result = get_csvs(well_path,
                                  filebases,
                                  fin_wells,
                                  )
            filebases = csv_result['bases']
            fin_wells = csv_result['wells']

    # For all experiment wells imaged so far, run R script
    if filebases:
        gain_dict = run_r(filebases,
                          fin_wells,
                          r_script,
                          imaging_dir,
                          initialgains_file,
                          gain_dict
                          )
    return gain_dict

def parse_gain(gain_dict, template=None):
    green_sorted = defaultdict(list)
    medians = defaultdict(int)
    for i, c in enumerate(['green', 'blue', 'yellow', 'red']):
        mlist = []
        for k, v in gain_dict.iteritems():
            # Sort gain data into a list dict with well as key and where the
            # value is a list with a gain value for each channel.
            if c == 'green':
                # Round gain values to multiples of 10 in green channel
                green_val = int(round(int(v[i]), -1))
                if template:
                    for well in template[k]:
                        green_sorted[green_val].append(well)
                else:
                    green_sorted[green_val].append(k)
            else:
                # Find the median value of all gains in
                # blue, yellow and red channels.
                mlist.append(int(v[i]))
                medians[c] = int(np.median(mlist))
    return {'green':green_sorted, 'medians':medians}

def send_com(com_list,
             end_com_list,
             sock,
             start_com,
             cstart,
             stop_cam_com,
             stop_com,
             imaging_dir,
             last_field,
             end_63x,
             r_script,
             initialgains_file,
             saved_gains,
             template,
             job_list,
             pattern,
             first_job,
             coords,
             stage1=None,
             stage3=None,
             stage4=None
             ):
    for com, end_com in zip(com_list, end_com_list):
        # Send CAM list for the gain job to the server (stage1).
        # Send gain change command to server in the four channels (stage3/4).
        # Send CAM list for the experiment jobs to server (stage3/4).
        # Reset gain_dict for each iteration.
        gain_dict = defaultdict(list)
        com = '/cli:1 /app:matrix /cmd:deletelist\n' + com
        print(com)
        sock.send(com)
        time.sleep(3)
        # Start scan.
        print(start_com)
        sock.send(start_com)
        time.sleep(7)
        # Start CAM scan.
        print(cstart)
        sock.send(cstart)
        time.sleep(3)
        stage5 = True
        while stage5:
            print('Waiting for images...')
            reply = sock.recv_timeout(120, ['image--'])
            for line in reply.splitlines():
                if stage1:
                    print('Stage1')
                    gain_dict = get_gain(line,
                                         imaging_dir,
                                         last_field,
                                         end_63x,
                                         sock,
                                         stop_com,
                                         r_script,
                                         initialgains_file,
                                         gain_dict
                                         )
                    #print(gain_dict) #testing
                    if not saved_gains:
                        saved_gains = gain_dict
                    if saved_gains:
                        #print(saved_gains) #testing
                        saved_gains.update(gain_dict)
                        header = ['well', 'green', 'blue', 'yellow', 'red']
                        csv_name = 'output_gains.csv'
                        write_csv(os.path.normpath(os.path.join(imaging_dir,
                                                                csv_name
                                                                )
                                                   ),
                                  saved_gains,
                                  header
                                  )
                        com_result = gen_com(gain_dict,
                                             template,
                                             job_list,
                                             pattern,
                                             first_job,
                                             coords=coords
                                             )
                        late_com_list = com_result['com']
                        late_end_com_list = com_result['end_com']
                else:
                    if stage3:
                        print('Stage3')
                        img_saving = False
                    if stage4:
                        print('Stage4')
                        img_saving = True
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
                            except TypeError as e:
                                error = True
                                count += 1
                                time.sleep(1)
                                print('No images yet... but maybe later?' , e)
                if all(test in line for test in end_com):
                    stage5 = False
        # Stop scan
        #print(stop_cam_com)
        #sock.send(stop_cam_com)
        #time.sleep(5)
        print(stop_com)
        sock.send(stop_com)
        time.sleep(6) # Wait for it to come to complete stop.
        if gain_dict and stage1:
            send_com(late_com_list,
                     late_end_com_list,
                     sock,
                     start_com,
                     cstart,
                     stop_cam_com,
                     stop_com,
                     imaging_dir,
                     last_field,
                     end_63x,
                     r_script,
                     initialgains_file,
                     saved_gains,
                     template,
                     job_list,
                     pattern,
                     first_job,
                     coords,
                     stage1=False,
                     stage3=stage3,
                     stage4=stage4
                     )

def main(argv):
    """Main function"""

    try:
        opts, args = getopt.getopt(argv, 'hi:', ['help',
                                                 'input=',
                                                 'wdir=',
                                                 'std=',
                                                 'gainfile=',
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
                                                 'uvaf',
                                                 'gain'
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
    initialgains_file = os.path.normpath(os.path.join(working_dir,
                                                            '10x_gain.csv'))
    last_well = 'U00--V00'
    last_field = 'X01--Y01'
    template_file = None
    coord_file = None
    input_gain = None
    host = ''
    end_10x = False
    end_40x = False
    end_63x = False
    gain_only = False
    first_job = 1
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
        elif opt in ('--gainfile'):
            initialgains_file = os.path.normpath(arg)
        elif opt in ('--finwell'):
            last_well = arg # 'U00--V00'
        elif opt in ('--finfield'):
            last_field = arg # 'X00--Y00'
        elif opt in ('--coords'):
            coord_file = os.path.normpath(arg) #
        elif opt in ('--host'):
            host = arg
        elif opt in ('--inputgain'):
            input_gain = arg
        elif opt in ('--template'):
            template_file = arg
        elif opt in ('--10x'):
            end_10x = True
        elif opt in ('--40x'):
            end_40x = True
        elif opt in ('--63x'):
            end_63x = True
        elif opt in ('--uvaf'):
            first_job = 1
        elif opt in ('--gain'):
            gain_only = True
        else:
            assert False, 'Unhandled option!'

    # Paths
    r_script = os.path.normpath(os.path.join(working_dir, 'gain.r'))

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
    job_63x = ['job10', 'job11', 'job12']
    pattern_63x = 'pattern3'
    job_dummy_10x = 'dummy10x'
    pattern_dummy_10x = 'pdummy10x'
    pattern_dummy_40x = 'pdummy40x'

    pattern_g = pattern_g_10x

    # Lists and strings for storing command strings.
    com_list = []
    end_com_list = []
    com = ''
    end_com = []

    # Booleans etc to control flow.
    stage1 = True
    stage2 = True
    stage3 = True
    stage4 = False
    stage5 = False
    if end_10x:
        end_40x = False
        end_63x = False
        pattern_g = pattern_g_10x
        job_list = job_10x
        pattern = pattern_10x
    elif end_40x:
        end_10x = False
        end_63x = False
        pattern_g = pattern_g_40x
        job_list = job_40x
        pattern = pattern_40x
    if coord_file:
        end_63x = True
        coords = read_csv(coord_file, 'fov', ['dxPx', 'dyPx'])
    else:
        coords = None
    if end_63x:
        end_10x = False
        end_40x = False
        stage3 = False
        stage4 = True
        pattern_g = pattern_g_63x
        job_list = job_63x
        pattern = pattern_63x
    if gain_only:
        stage3 = False
        stage4 = False
    if input_gain:
        stage1 = False
    wells = []
    if template_file:
        template = read_csv(template_file, 'gain_from_well', ['well'])
        last_well = sorted(template.keys())[-1]
        # Selected wells from template file.
        wells = sorted(template.keys())
    else:
        template = None
        # All wells.
        for u in range(int(get_wfx(last_well))):
            for v in range(int(get_wfy(last_well))):
                wells.append('U0' + str(u) + '--V0' + str(v))
    # Selected objective gain job cam command in wells.
    for well in wells:
        for i in range(2):
            com = gen_cam_com(com, pattern_g, well, i, i, 'true', 0, 0)
            end_com = ['CAM',
                       well,
                       'E0' + str(2),
                       'X0{}--Y0{}'.format(i, i)
                       ]
        com_list.append(com)
        end_com_list.append(end_com)
        com = ''

    if end_10x or end_40x:
        com = ''.join(com_list)
        com_list = []
        com_list.append(com)
        end_com_list = []
        end_com_list.append(end_com)

    # commands
    start_com = '/cli:1 /app:matrix /cmd:startscan\n'
    stop_com = '/cli:1 /app:matrix /cmd:stopscan\n'
    stop_cam_com = '/cli:1 /app:matrix /cmd:stopcamscan\n'
    cstart = camstart_com()

    # Create socket
    sock = Client()
    # Port number
    port = 8895
    # Connect to server
    sock.connect(host, port)

    # lists for keeping csv file base path names and
    # corresponding well names
    filebases = []
    fin_wells = []

    # dicts of lists to store wells with gain values for the four channels.
    gain_dict = defaultdict(list)
    saved_gains = defaultdict(list)

    if input_gain:
        gain_dict = read_csv(input_gain,
                             'well',
                             ['green', 'blue', 'yellow', 'red']
                             )
        com_result = gen_com(gain_dict,
                             template,
                             job_list,
                             pattern,
                             first_job,
                             coords=coords
                             )
        com_list = com_result['com']
        end_com_list = com_result['end_com']

    if stage1 or stage3 or stage4:
        send_com(com_list,
                 end_com_list,
                 sock,
                 start_com,
                 cstart,
                 stop_cam_com,
                 stop_com,
                 imaging_dir,
                 last_field,
                 end_63x,
                 r_script,
                 initialgains_file,
                 saved_gains,
                 template,
                 job_list,
                 pattern,
                 first_job,
                 coords,
                 stage1=stage1,
                 stage3=stage3,
                 stage4=stage4
                 )

    print('\nExperiment finished!')

if __name__ =='__main__':
    main(sys.argv[1:])
