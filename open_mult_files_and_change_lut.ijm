setBatchMode(true)

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

pathLUTs = topDir+"luts/";
File.makeDirectory(pathLUTs);

fileArray = newArray();
fileArray = listFiles(dirChosen, topDir, ".+\.tif$", fileArray);

for (i = 0; i < fileArray.length; i++) {

	print(fileArray[i]);
	open(fileArray[i]);

	if ((2048 != getWidth()) || (2048 != getHeight())) {
		close();
	} else {
	
	channelIndex = indexOf(fileArray[i], "--C");
	channelString = substring(fileArray[i], channelIndex+3, channelIndex+5);
	wellXIndex = indexOf(fileArray[i], "--U");
	wellX = substring(fileArray[i], wellXIndex+3, wellXIndex+5);
	wellYIndex = indexOf(fileArray[i], "--V");
	wellY = substring(fileArray[i], wellYIndex+3, wellYIndex+5);
	xFieldIndex = indexOf(fileArray[i], "--X");
	yFieldIndex = indexOf(fileArray[i], "--Y");
	xField = substring(fileArray[i], xFieldIndex+3, xFieldIndex+5);
	yField = substring(fileArray[i], yFieldIndex+3, yFieldIndex+5);

	if (channelString == "00") {
		run("Blue");
	} else if (channelString == "01") {
		run("Green");
	} else if (channelString == "02" || channelString == "03") {
		run("Red");
	}
	
	run("8-bit");
	saveAs("Jpeg", pathLUTs+"U"+wellX+"--V"+wellY+"--X"+xField+"--Y"+yField+
			"--C"+channelString+".jpg");
	close("*");
	}
}
print("Analysis finished!");