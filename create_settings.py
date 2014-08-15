import csv
import numpy

working_dir = sys.argv[1]
gain_file = sys.argv[2]
xml_input = sys.argv[3]
lrp_input = sys.argv[4]
gains = []
with open(gain_file) as _file:
    reader = csv.DictReader(_file)
    for i in reader:
        gains.append(i)

def create_dict(input_list, output_dict, key, value):
    for i in input_list:
        output_dict[i[key]] = i[value]
    return output_dict

green = {}
blue = {}
yellow = {}
red = {}
green = create_dict(gains, green, "well", "green")
blue = create_dict(gains, blue, "well", "blue")
yellow = create_dict(gains, yellow, "well", "yellow")
red = create_dict(gains, red, "well", "red")

def round_values(input_dict, output_list):
    for k, v in input_dict.iteritems():
        input_dict[k] = int(round(int(v), -1))
        output_list.append(v)
    return

green_list = []
green_list = round_values(green, green_list)

green_unique = sorted(set(green_list))

def find_median(input_list, input_dict):
    round_values(input_dict, input_list)
    median = int(numpy.median(input_list))
    return median

blue_list = []
blue_median = find_median(blue_list, blue)
yellow_list = []
yellow_median = find_median(yellow_list, yellow)
red_list = []
red_median = find_median(red_list, red)

# For each pos in green_unique, copy job, change gain in channels,
# assign the job if value of green_unique matches any value in green
i = 1
for value in green_unique:
    #copy <LDM_Block_Sequence_Block 2 BlockID=str(n)> to
    # <LDM_Block_Sequence_Block tot+i BlockID=str(n+1)>
    #copy <LDM_Block_Sequence_Element 2 BlockID=str(n) ElementID=str(p)> to
    # <LDM_Block_Sequence_Element tot+i BlockID=str(n+1) ElementID=str(p+1)>
    #set gain for job tot+i
    #green_detector = value
    #blue_detector = blue_median
    #yellow_detector = yellow_median
    #red_detector = red_median
    for k, v in green.iteritems():
        if v == value:
            #assign job tot+i to well k
    i += 1
