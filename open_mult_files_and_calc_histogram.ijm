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
// Set path to image directory.
dirChosen = getDirectory("Choose a Directory ");
topDir = dirChosen;

// Open all images in for loop.
File.saveString(fileString, topDir+"files.txt");
listFiles(dirChosen, topDir);
filesInString = File.openAsString(topDir + "files.txt");
fileArray = split(filesInString,"\n");
for (j = 0; j < fileArray.length; j++) {
	imagePath = fileArray[j];

	// Open image.
	open(imagePath);
	
	// Set image name.
	imageName = getTitle();

	gainStart = 600;
	channelStart = 25;
	gainStep = 30;
	channelIndex = indexOf(imageName, "--C");
	channel = parseInt(substring(imageName, channelIndex+3, channelIndex+5));
	gain=gainStart+(channel-channelStart)*gainStep;
	
	nBins = 256;
	getHistogram(values, counts, nBins);
	d=File.open(topDir+imageName+"_"+gain+".csv"); 
	print(d, "Bin,Count"); 
	for (k=0; k<nBins; k++) { 
		print(d, k+","+counts[k]); 
	}
	File.close(d);
	close();
}
print("Analysis done!")
