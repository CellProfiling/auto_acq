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

wellsNo = getNumber("Enter number of wells in the analysis.", 96);
fieldsNo = getNumber("Enter number of fields per well.", 4);
channelsNo = 4;

count2 = 0;

while(count2 < wellsNo*fieldsNo*channelsNo) {
	fileArray = newArray();
    fileArray = listFiles(dirChosen, topDir, ".+\.tif$", fileArray);

    while (fileArray.length != 0) {

	    print(fileArray[0]);
	    open(fileArray[0]);

	    if ((512 > getWidth()) || (512 > getHeight())) {
		    close();
            err=File.rename(fileArray[0], fileArray[0]+".bak");
	    } else {
	
	        channelIndex = indexOf(fileArray[0], "--C");
	        channelString = substring(fileArray[0], channelIndex+3, channelIndex+5);
	        wellXIndex = indexOf(fileArray[0], "--U");
	        wellX = substring(fileArray[0], wellXIndex+3, wellXIndex+5);
	        wellYIndex = indexOf(fileArray[0], "--V");
	        wellY = substring(fileArray[0], wellYIndex+3, wellYIndex+5);
	        xFieldIndex = indexOf(fileArray[0], "--X");
	        yFieldIndex = indexOf(fileArray[0], "--Y");
	        xField = substring(fileArray[0], xFieldIndex+3, xFieldIndex+5);
	        yField = substring(fileArray[0], yFieldIndex+3, yFieldIndex+5);

	        if (channelString == "00") {
		        run("Green");
	        } else if (channelString == "01") {
		        run("Blue");
	        } else if (channelString == "02") {
		        run("Yellow");
	        } else if (channelString == "03") {
		        run("Red");
	        }
	
	        run("8-bit");
	        saveAs("PNG", pathLUTs+"U"+wellX+"--V"+wellY+"--X"+xField+"--Y"+yField+
			        "--C"+channelString+".png");
	        close("*");
            err=File.rename(fileArray[0], fileArray[0]+".bak");
	    }
    }
}

print("Analysis finished!");