import csv

working_dir = sys.argv[1]
gain_file = sys.argv[2]

reader = csv.DictReader(file_data, ("title", "value"))
for i in reader:
  list_of_stuff.append(i)
