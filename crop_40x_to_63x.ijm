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

fileArray = newArray();
fileArray = listFiles(dirChosen, topDir, ".+C00\\.png$", fileArray);

// Write existing coordinate file contents to new file.
if (File.exists(topDir+"63x_coords.csv") == true) {
	fileString = File.openAsString(topDir+"63x_coords.csv");
} else {
	fileString = "fov,dxM,dyM,dxPx,dyPx";
}
success = File.delete(topDir+"63x_coords.csv");
// Open file to write output to.
output = File.open(topDir+"63x_coords.csv");
print(output, fileString);

// For-loop ends at the bottom of the code, as most of it is done on each image.
for (j = 0; j < fileArray.length; j++) {

	//Open image.
	open(fileArray[j]);

	//Get image name.
	name = getTitle();

	//Image size (pixels)
	width = getWidth;

	//Close the image if it does not have the correct image size in pixels.
	if (width < 512) {
		print("Not correct size of image!");
		close();
	} else {

		//Well, field and channel
		xWellIndex = indexOf(name, "U");
		yWellIndex = indexOf(name, "--V");
		xWell = substring(name, xWellIndex+1, xWellIndex+3);
		yWell = substring(name, yWellIndex+3, yWellIndex+5);
		wellNumber = (8 * (parseInt(xWell)) + (parseInt(yWell)))+1;
		xFieldIndex = indexOf(name, "--X");
		yFieldIndex = indexOf(name, "--Y");
		xField = substring(name, xFieldIndex+3, xFieldIndex+5);
		yField = substring(name, yFieldIndex+3, yFieldIndex+5);
		cIndex = indexOf(name, "--C");
		channel = substring(name, cIndex+3, cIndex+5);

		open(replace(fileArray[j], "--C"+channel, "--C0"+3+""));
		if (xWell == "00" && yWell == "00" && xField == "00" && yField == "00") {
			makeRectangle(0, 0, width/2, width/2);
			run("Draw");
			makeRectangle(width/2, width/2, width/2, width/2);
			run("Draw");
			saveAs("PNG", topDir+"start_position.png");
			close;
			open(replace(fileArray[j], "--C"+channel, "--C0"+3+""));
		}
		run("Merge Channels...", "c1="+replace(name, "--C"+channel, "--C0"+3+"")+" c2="+name+"");

		// Make selection rectangle
		makeRectangle(width/2, width/2, round(width*164/387.5), round(width*164/387.5));
		
		// waitForUser(title, message)
		waitForUser("Well: "+wellNumber+" Fieldx: "+xField+" Fieldy: "+yField+"",
			"Please select the area to be cropped. When you are done, click ok.");
		
		// Get selection coordinates
		getSelectionCoordinates(roiX, roiY);
		
		if(!getBoolean("Do you want to save the position of the cropped image for 63x imaging? Cancel will quit the macro.")) {
			close;
			err=File.rename(fileArray[j], fileArray[j]+".bak");
		} else {
            
		
		
		    //Testing
		    for (k=0; k<roiX.length; k++) {
			    print(k+" "+roiX[k]+" "+roiY[k]);
		    }	

		    for (k = 0; k < 4; k++) {
			    imageChannel = replace(fileArray[j], "--C"+channel, "--C0"+k+"");
			    open(imageChannel);
			    makeRectangle(roiX[0], roiY[0], round(width*164/387.5), round(width*164/387.5));
			    run("Crop");
			    saveAs("Tiff", ""+replace(imageChannel, ".png", "_cropped.tif"));
			    close();
			    err=File.rename(replace(imageChannel, ".png", "_cropped.tif"), replace(imageChannel, ".png", "_cropped.tif")+".bak");
			    //err=File.rename(replace(imageChannel, ".ome.tif", "_cropped.ome.tif"), replace(replace(imageChannel, ".ome.tif", "_cropped.ome.tif"), "image--.+", "/cropped/"+replace(replace(imageChannel, ".ome.tif", "_cropped.ome.tif"), ".+image--", "image--")));
		    }

		    // A half 63x zoom 1.5 image is ~433 px on a 40x zoom 1 image.
		    // 0.1892 um/px for 40x zoom 1. 0.0801 um/px for 63x zoom 1.5.
    		// Difference in XY after changing from 40x to 63x oil objective
	    	// in Y is +17.0 um (90 px for 40x zoom 1) on the image, or -17.0 um
	    	// on the table. Don't need to correct for that if start coordinates are
	    	// synced instead.

            //pixels in a 63x zoom 1.5 image
	    	dxPx = round((1024 - roiX[0] - 433) * (0.1892/0.0801));
	    	dyPx = round((1024 - roiY[0] - 433) * (0.1892/0.0801));
		
	    	//m
	    	dxM = (dxPx * 0.0801)/1000000;
	    	dyM = (dyPx * 0.0801)/1000000;

	    	//Testing
	    	print("xWell: "+xWell);
	    	print("yWell: "+yWell);
		
	    	print(output, "U"+xWell+"--V"+yWell+"--X"+xField+"--Y"+yField+","+dxM+","+dyM+","+dxPx+","+dyPx);
	    	//Close the image.
        	close();
        	err=File.rename(fileArray[j], fileArray[j]+".bak");
	    }
    }
}

File.close(output);
print("Analysis finished!");
