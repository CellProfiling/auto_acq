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

path = topDir+"combos/";
File.makeDirectory(path);

fileArray = newArray();
fileArray = listFiles(dirChosen, topDir, ".+green\.tif$", fileArray);

for (i = 0; i < fileArray.length; i++) {

	print(fileArray[i]);
	open(fileArray[i]);
	imDir = getInfo("image.directory");
	imGreenName = getInfo("image.filename");
	imBlueName = replace(imGreenName, "green", "blue");
	imRedName = replace(imGreenName, "green", "red");
	imYellowName = replace(imGreenName, "green", "yellow");
	imRedGreenName = replace(imGreenName, "green.tif", "red_green.png");
	imBlueRedGreenName = replace(imGreenName, "green.tif", "blue_red_green.png");
	//imPNGName = replace(imFileName, tif, png);

	if ((2048 != getWidth()) || (2048 != getHeight())) {
		close();
	} else {
		run("Green");
		//print(imFileName);
		//print(imRedName);
		open(imDir+imRedName);
		run("Red");
		run("Merge Channels...", "c1=imRedName c2=imGreenName keep");
		saveAs("PNG", path+imRedGreenName);
		close();
		open(imDir+imBlueName);
		run("Blue");
		run("Merge Channels...", "c1=imRedName c2=imGreenName c3=imBlueName keep");
		saveAs("PNG", path+imBlueRedGreenName);
		close("*");
	}
}
print("Analysis finished!");