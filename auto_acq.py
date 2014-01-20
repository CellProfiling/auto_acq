# Plan: For all images from gain-job, do histogram, select JobName.
# Get x_well and y_well from image filename,
# then loop through xml-file and get/set at matching WellX and WellY.
# From xml-template-files get corresponding JobId (from lrp-file),
# WellX and WellY (from xml-file),
# set at all four fields (FieldX, FieldY) with correct JobName, JobId
# and JobAssigned, save as new xml-file.
# XML-template (and lrp) should come from saved template in
# microscope for correct experiment.

from PIL import Image

image_file = '/home/martin/Skrivbord/Gain/CAM1--2013_03_02_15_37_32/slide--S00/chamber--U00--V00/field--X00--Y00/image--L0000--S00--U00--V00--J102--E00--O00--X00--Y00--T0000--Z00--C15.ome.tif'

image = Image.open(image_file)

histo = image.histogram()

channel_string = image_file[len(image_file)-10:len(image_file)-8]

channel_number = int(channel_string)

# Well id from image file name.
y_well = image_file[len(image_file)-53:len(image_file)-51]
x_well = image_file[len(image_file)-58:len(image_file)-56]
well_number = x_well*8+y_well+1

well_job_name_dict = {}
well_job_name_dict[well_number] = 'Job16'

job_number_string = well_job_name_dict[well_number][-2:]

job_number = int(job_number_string)

# Check which image has best saturation
# and assign job name to the corresponding well.
if (histo[-1] >=13) & (channel_number+1 <= job_number):
    job_number = channel_number+1
    well_job_name_dict[well] = 'Job'+str(job_number)
