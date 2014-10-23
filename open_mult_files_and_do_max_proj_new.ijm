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

pathMaxProjs = topDir+"maxprojs/";
File.makeDirectory(pathMaxProjs);

wellsNo = 
fieldsNo = 
channelsNo = 

count = 0;

while(count < wellNo*fieldNo*channelsNo) {

	fileArray = newArray();
	fileArray = listFiles(dirChosen, topDir, ".+\.tif$", fileArray);

	while (fileArray.length != 0) {
	
	    jobIndex = indexOf(fileArray[0], "--J");
        job = substring(fileArray[0], jobIndex+3, jobIndex+5);
	    channelIndex = indexOf(fileArray[0], "--C");
	    channelString = substring(fileArray[0], channelIndex+3, channelIndex+5);
	    wellXIndex = indexOf(fileArray[0], "--U");
	    wellX = substring(fileArray[0], wellXIndex+3, wellXIndex+5);
	    wellYIndex = indexOf(fileArray[0], "--V");
	    wellY = substring(fileArray[0], wellYIndex+3, wellYIndex+5);

	    imagesToStack = newArray();
	    newFileArray = newArray();
	    //testing
	    print("Empty newFileArray");
	    print(newFileArray.length);

	    for (i = 0; i < fileArray.length; i++) {
		    if (matches(fileArray[i], ".+--J"+job+".+--U"+wellX+".+--V"+wellY+".+--C"+
			    	channelString+".+\.tif$")) {
			    imagesToStack = addToArray(fileArray[i], imagesToStack,
			                    (imagesToStack.length));
		    } else {
			    newFileArray = addToArray(fileArray[i], newFileArray,
			                    (newFileArray.length));
		    }
	    }
	    //testing
	    print("Filling newFileArray");
	    print(newFileArray.length);

	    fileArray = newFileArray;
        if(imagesToStack.length == fieldsNo) {
	    for (i = 0; i < imagesToStack.length; i++) {
		    open(imagesToStack[i]);
            count++;
		    if ((512 != getWidth()) || (512 != getHeight())) {
			    close();
		    }
	    }
        }
	    run("Images to Stack", "name=Stack title=[] use");
	    run("Z Project...", "projection=[Max Intensity]");
	    saveAs("Tiff", pathMaxProjs+"U"+wellX+"--V"+wellY+"--C"+
	            channelString+".tif");
	    close("*");
    }
}
print("Analysis finished!");