# Make different imaging_dir? 10x, 40x etc.
import sys
import getopt
import subprocess
import re
import time

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
#first_std_dir = sys.argv[3]
#sec_std_dir = sys.argv[4]
#first_initialgains_file = sys.argv[5]
#sec_initialgains_file = sys.argv[6]
#last_well = sys.argv[7] #U00V00
#last_field = sys.argv[8] #X00Y00

if __name__ =='__main__':
    main(sys.argv[1:])

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

while stage1:
    
