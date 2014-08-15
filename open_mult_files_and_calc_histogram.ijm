setBatchMode(true)

// From OpenSeriesUsingFilter.txt
//Recursive file listing.
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
	
	//does name match regex search?
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

// Open all images in for loop.
fileArray = newArray();
fileArray = listFiles(dirChosen, topDir, ".+\.tif$", fileArray);
for (j = 0; j < fileArray.length; j++) {

	// Open image.
	open(fileArray[j]);

	channelIndex = indexOf(fileArray[j], "C");
	channelString = substring(fileArray[j], channelIndex+1, channelIndex+3);
	wellXIndex = indexOf(fileArray[j], "U");
	wellX = substring(fileArray[j], wellXIndex+1, wellXIndex+3);
	wellYIndex = indexOf(fileArray[j], "V");
	wellY = substring(fileArray[j], wellYIndex+1, wellYIndex+3);
	
	nBins = 256;
	getHistogram(values, counts, nBins);
	d=File.open(topDir+"U"+wellX+"--V"+wellY+"--C"+channelString+".ome.csv");
	print(d, "bin,count"); 
	for (k=0; k<nBins; k++) { 
		print(d, k+","+counts[k]); 
	}
	File.close(d);
	close();
}
print("Analysis done!")
