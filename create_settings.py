import csv

working_dir = sys.argv[1]
gain_file = sys.argv[2]
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

green_list = []

for k, v in green.iteritems():
    v1 = int(v)
    v2 = round(v1, -1)
    print(v+' '+str(v1)+' '+str(v2))
    green_list.append(v2)

green_unique = set(green_list)
