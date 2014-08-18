import csv
from lxml import etree

working_dir = sys.argv[1]
coord_file = sys.argv[2]
xml_input = sys.argv[3]

coords = []
with open(coord_file) as _file:
    reader = csv.DictReader(_file)
    for i in reader:
        coords.append(i)

def create_dict(input_list, output_dict, key, value):
    for i in input_list:
        output_dict[i[key]] = i[value]
    return output_dict

# Sort coord data into dicts
dxs = {}
dys = {}

dxs = create_dict(coords, dxs, "fov", "dx")
dys = create_dict(coords, dys, "fov", "dy")

xml_doc = etree.parse(xml_input)

enable = etree.parse('/home/martin/Dev/auto_acq/enable.xsl')

t_enable = etree.XSLT(enable)

# For each fov in dxs, change x/y coordinates
for k, v in dxs.iteritems():
    # change xcoord in well k
    wellx = str(int(k[1:3])+1)
    welly = str(int(k[6:8])+1)
    fieldx = str(int(k[11:13])+1)
    fieldy = str(int(k[16:18])+1)
    dx = v
    dy = dys[k]
    xml_doc = t_enable(xml_doc, WELLX=wellx, WELLY=welly, FIELDX=fieldx,
            FIELDY=fieldy, DX=str(dx), DY=str(dy))

# Save the xml to file
xml_doc.write(xml_input[0:-4]+'_new.xml', pretty_print=False)
