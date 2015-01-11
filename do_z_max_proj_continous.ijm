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

wellsNo = getNumber("Enter number of wells in the analysis.", 96);
fieldsNo = getNumber("Enter number of fields per well.", 2);
slices = getNumber("Enter number of slices per field of view.", 25);
channelsNo = getNumber("Enter number of channels per field of view.", 32);

count2 = 0;
oldCount = 0;

while(count2 < wellsNo*fieldsNo*slices*channelsNo) {

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
		fieldXIndex = indexOf(fileArray[0], "--X");
		fieldX = substring(fileArray[0], fieldXIndex+3, fieldXIndex+5);
		fieldYIndex = indexOf(fileArray[0], "--Y");
		fieldY = substring(fileArray[0], fieldYIndex+3, fieldYIndex+5);

		imagesToStack = newArray();
		newFileArray = newArray();
		//testing
		print("Empty newFileArray");
		print(newFileArray.length);

		for (i = 0; i < fileArray.length; i++) {
			if (matches(fileArray[i], ".+--U"+wellX+"--V"+wellY+"--J"+job+".+--X"+fieldX+"--Y"+fieldY+".+--C"+channelString+".+\.tif$")) {
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
		
		if(imagesToStack.length == slices) {
			oldCount = count2;
			for (i = 0; i < imagesToStack.length; i++) {
				open(imagesToStack[i]);
				if ((512 > getWidth()) || (512 > getHeight())) {
					close();
				} else {
		    		count2++;
		    		print(count2);
		    	}
			}
		}

		if(oldCount+slices==count2) {
			run("Images to Stack", "name=Stack title=[] use");
			run("Z Project...", "projection=[Max Intensity]");
			pathProjImage = pathMaxProjs+"U"+wellX+"--V"+wellY+"--X"+fieldX+"--Y"+fieldY+"--C"+
	    		    channelString+".png";
			saveAs("PNG", pathProjImage);
			close("*");
			err=File.rename(pathProjImage, pathProjImage+".bak");
		}
		for (i = 0; i < imagesToStack.length; i++) {
	    	err=File.rename(imagesToStack[i], imagesToStack[i]+".bak");
	    }
	}
}
print("Analysis finished!");