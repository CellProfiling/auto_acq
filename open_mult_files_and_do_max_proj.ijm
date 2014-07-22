setBatchMode(true)

// From OpenSeriesUsingFilter.txt
//Recursive file listing. Saves the paths in a text file.
count = 1;
fileString = "";
function listFiles(dir, rootDir) {
	fileList = getFileList(dir);
	if (File.exists(rootDir+"files.txt")!= 1) {
		File.saveString("", rootDir+"files.txt");
	}
	fileString = File.openAsString(rootDir + "files.txt");
	for (i=0; i<fileList.length; i++) {
		if (endsWith(fileList[i], "/")) {
			listFiles(""+dir+fileList[i], rootDir);
		} else {
			if (filter(i, fileList[i])) {
				//Testing
				print((count++) + ": " + dir + fileList[i]);
				fileString = fileString + dir + fileList[i] + "\n";
				File.saveString(fileString, rootDir+"files.txt");
			}
		}
	}
}

// From OpenSeriesUsingFilter.txt
// Filter files in chosen directory and sub-directories to use for analysis,
// by conditions set below.
function filter(i, name) {
	// is directory?
	if (endsWith(name, File.separator)) return false;

	// is tiff?
	if (!endsWith(name, ".tif")) return false;

	// ignore text files
	// if (endsWith(name, ".txt")) return false;

	// does name contain both "Series002" and "ch01"
	// if (indexOf(name, "Series002") == -1) return false;
	// if (indexOf(name, "ch01") == -1) return false;

	// does name contain "--C00"?
	//if (indexOf(name, "--C00") == -1) return false;
	//if (indexOf(name, "--C00") == -1) return false;

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

// Open all images in for loop.
File.saveString(fileString, topDir+"files.txt");
listFiles(dirChosen, topDir);
filesInString = File.openAsString(topDir + "files.txt");
fileArray = split(filesInString,"\n");

while (fileArray.length != 0) {

//for (j = 0; j < fileArray.length; j++) {
	imagePath = fileArray[0];

	// Open image.
	open(imagePath);
	
	// Get image name.
	imageName = getTitle();

	// Get image directory
	imageDir = getDirectory("image");
	
	channelIndex = indexOf(imageName, "--C");
	channelString = substring(imageName, channelIndex+3, channelIndex+5);
	//channel = parseInt(substring(imageName, channelIndex+3, channelIndex+5));
	wellXIndex = indexOf(imageName, "--U");
	wellX = substring(imageName, wellXIndex+3, wellXIndex+5);
	wellYIndex = indexOf(imageName, "--V");
	wellY = substring(imageName, wellYIndex+3, wellYIndex+5);

	close();

	imagesToStack = newArray();
	newFileArray = newArray();
	//testing
	print("Empty newFileArray");
	print(newFileArray.length);

	for (i = 0; i < fileArray.length; i++) {
		image2Path = fileArray[i];
		// Open image.
		open(image2Path);
		// Get image name.
		image2Name = getTitle();
		image2ChannelString = substring(image2Name, channelIndex+3, channelIndex+5);
		image2WellX = substring(image2Name, wellXIndex+3, wellXIndex+5);
		image2WellY = substring(image2Name, wellYIndex+3, wellYIndex+5);
		if (wellX == image2WellX && wellY == image2WellY && channelString == image2ChannelString) {
			imagesToStack = addToArray(image2Path, imagesToStack, (imagesToStack.length));
		} else {
			newFileArray = addToArray(image2Path, newFileArray, (newFileArray.length));
		}
		close();
	}
	//testing
	print("Filling newFileArray");
	print(newFileArray.length);

	fileArray = newFileArray;

	for (i = 0; i < imagesToStack.length; i++) {
		imagePath = imagesToStack[i];
		// Open image.
		open(imagePath);
	}
	run("Images to Stack", "name=Stack title=[] use");
	run("Z Project...", "projection=[Max Intensity]");
	saveAs("Tiff", pathMaxProjs+"U"+wellX+"--V"+wellY+"--C"+channelString+".tif");
	close();
	close();
}
print("Analysis finished!");
