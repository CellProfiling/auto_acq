from PIL import Image

image_file = '/home/martin/Skrivbord/Gain/CAM1--2013_03_02_15_37_32/slide--S00/chamber--U00--V00/field--X00--Y00/image--L0000--S00--U00--V00--J102--E00--O00--X00--Y00--T0000--Z00--C15.ome.tif'

image = Image.open(image_file)

histo = image.histogram()

channel_string = image_file[len(image_file)-10:len(image_file)-8]

channel_number = int(channel_string)

job_number_string = well_job_name_dict[well][-2:]

job_number = int(job_number_string)

# Fix well id from image file name.
#well = image_file[len(image_file)-10:len(image_file)-8]

well_job_name_dict = {}
well_job_name_dict[well] = 'Job16'

# Check which image has best saturation and assign job name to the corresponding well.
if (histo[-1] >=13) & (channel_number+1 <= job_number):
    job_number = channel_number+1
    well_job_name_dict[well] = 'Job'+str(job_number)
