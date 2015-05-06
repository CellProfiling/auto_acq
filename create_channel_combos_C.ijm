//setBatchMode(true)

// From OpenSeriesUsingFilter.txt
// Recursive file listing.
count = 1;
function listFiles(dir, rootDir, search, array) {
	fileList = getFileList(dir);
	for (i=0; i<fileList.length; i++) {
		if (endsWith(fileList[i], "/")) {
			array = listFiles(""+dir+fileList[i], rootDir, search, array);
		} else {
			if (filter(i, fileList[i], search)) {
				pathToString = dir + fileList[i];
				array = addToArray(pathToString, array, array.length);
				//testing
				print((count++) + ": " + array[array.length-1]);
			}
		}
	}
	return array;
}

// From OpenSeriesUsingFilter.txt
// Filter files in chosen directory and sub-directories to use for analysis,
// by conditions set below.
function filter(i, name, search) {
	// is directory?
	if (endsWith(name, File.separator)) return false;
	
	// does name match regex search?
	if (matches(name, search) != true) return false;

	// open only first 10 images
	// if (i >= 10) return false;

	return true;
}

// From Array_Tools.ijm.
// Adds the value to the array at the specified position,
// expanding if necessary. Returns the modified array.
function addToArray(value, array, position) {
	if (position<lengthOf(array)) {
		array[position]=value;
    	} else {
    		temparray=newArray(position+1);
        	for (i=0; i<lengthOf(array); i++) {
        		temparray[i]=array[i];
        	}
        	temparray[position]=value;
        	array=temparray;
    	}
    	return array;
}

// Set path to image directory.
dirChosen = getDirectory("Choose a Directory ");
topDir = dirChosen;

path = topDir+"combos/";
File.makeDirectory(path);

fileArray = newArray();
fileArray = listFiles(dirChosen, topDir, ".+C00.+tif$", fileArray);

for (i = 0; i < fileArray.length; i++) {

	print(fileArray[i]);
	open(fileArray[i]);
	imDir = getInfo("image.directory");
	imGreenName = getInfo("image.filename");
	imBlueName = replace(imGreenName, "C00", "C01");
	imBlueGreenName = replace(imGreenName, "C00.ome.tif", "blue_green.png");

	//open("/home/martin/Skrivbord/ROI/field--X00--Y00/image--L0000--S00--U00--V00--J13--E00--O01--X00--Y00--T0000--Z00--C00.ome.tif");
	//run("Green");
	//open("/home/martin/Skrivbord/ROI/field--X00--Y00/image--L0000--S00--U00--V00--J13--E00--O01--X00--Y00--T0000--Z00--C01.ome.tif");
	//run("Blue");
	//run("Merge Channels...", "c2=image--L0000--S00--U00--V00--J13--E00--O01--X00--Y00--T0000--Z00--C00.ome.tif c3=image--L0000--S00--U00--V00--J13--E00--O01--X00--Y00--T0000--Z00--C01.ome.tif keep");
	//run("Close All");

	if ((2048 != getWidth()) || (2048 != getHeight())) {
		close();
	} else {
		run("Green");
		run("RGB Color");
		print(imDir+imBlueName);
		open(imDir+imBlueName);
		run("Blue");
		run("RGB Color");
		run("Merge Channels...", "c2=imGreenName c3=imBlueName");
		saveAs("PNG", path+imBlueGreenName);
		close("*");
	}
}
print("Analysis finished!");