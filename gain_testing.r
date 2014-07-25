## Author(s): Kalle von Feilitzen & Martin Hjelmare

# Gain calculation script
# Run with "Rscript path/to/script/gain.r path/to/working/dir/
# path/to/histogram-csv-filebase path/to/initialgains/csv-file"
# from linux command line.
# Repeat for each well.

# New arguments and input needed:
# inputGain, 1 per channel, so should be vector with 4 places
# first objective path/to/working/dir/
# second objective path/to/working/dir/
# first objective path/to/histogram-csv-filebase
# second objective path/to/histogram-csv-filebase
# initialgains for first objective
# initialgains for second objective

# Gain calculation script
#firstObjWorkPath <- commandArgs(TRUE)[1]
#firstObjHistoBase <- commandArgs(TRUE)[2]
#firstInitialgainsCSV <- commandArgs(TRUE)[3]
#inputGain <- commandArgs(TRUE)[4]
#secObjWorkPath <- commandArgs(TRUE)[5]
#secObjHistoBase <- commandArgs(TRUE)[6]
#secInitialgainsCSV <- commandArgs(TRUE)[7]

firstObjWorkPath <- "/home/martin/Skrivbord/test/10x/maxprojs/"
firstObjHistoBase <- "/home/martin/Skrivbord/test/10x/maxprojs/U00--V00--"
firstInitialgainsCSV <- "/home/martin/Dev/auto_acq/gain.csv"
secObjWorkPath <- "/home/martin/Skrivbord/test/63x/maxprojs/"
secObjHistoBase <- "/home/martin/Skrivbord/test/63x/maxprojs/U00--V00--"
secInitialgainsCSV <- "/home/martin/Dev/auto_acq/gain2.csv"

# Make function and call with the different objective arguments
# and with gain values from previous screening
# Return regression curv function as output
# Arguments to specify what is x and what is y in plot, regression etc
#func3 <- function(initGainsFile, input, objWorkPath, objHistoBase, onOff) {

gain <- list()
bins <- list()
gains <- list()

green <- 11;  # 11 images
blue <- 18;  	# 7 images
yellow <- 25;	# 7 images
red <- 32;		# 7 images
channel <- vector()
channel_name <- vector()
channel <- append(channel, rep(green, green-length(channel)))
channel_name <- append(channel_name, rep('green', green-length(channel_name)))
channel <- append(channel, rep(blue, blue-length(channel)))
channel_name <- append(channel_name, rep('blue', blue-length(channel_name)))
channel <- append(channel, rep(yellow, yellow-length(channel)))
channel_name <- append(channel_name, rep('yellow', yellow-length(channel_name)))
channel <- append(channel, rep(red, red-length(channel)))
channel_name <- append(channel_name, rep('red', red-length(channel_name)))
channels <- unique(channel)

for (i in 1:(length(channels))) {
  bins[[i]] <- vector()
  gains[[i]] <- vector()
}

setwd(firstObjWorkPath)
filebase <- firstObjHistoBase
# Initial gain values used
initialgains <- read.csv(firstInitialgainsCSV)$gain

# Create curve and function for each individual well
for (i in 1:32) {
  # Read histogram CSV file
  csvfile <- paste(filebase, "C", sprintf("%02d", i-1), ".ome.csv", sep="")
  csv <- read.csv(csvfile)
  csv1 <- csv[csv$count>0 & csv$bin>0,]
  bin1 <- csv1$bin
  count1 <- csv1$count
  # Only use values in interval 10-100
  binmax <- tail(csv$bin, n=1)
  csv2 <- csv[csv$count <= 100 & csv$count >= 10 & csv$bin < binmax,]
  bin2 <- csv2$bin
  count2 <- csv2$count
  # Plot values
  test <- 0
  png(filename=paste(filebase, "C", sprintf("%02d", i-1), ".ome.png", sep = ""))
  if (length(bin1) > 0) {
    plot(count1, bin1, log="xy")
  }
  # Fit curve
  sink("/dev/null")	# Suppress output
  curv <- tryCatch(nls(bin2 ~ A*count2^B, start=list(A = 1000, B=-1), trace=T), warning=function(e) NULL, error=function(e) NULL)
  sink()
  if (!is.null(curv)) {
    # Plot curve
    lines(count2, fitted.values(curv), lwd=2, col="green")
    # Find function and save gain value
    func <- function(val, A=coef(curv)[1], B=coef(curv)[2]) {A*val^B}
    chn <- which(channels==channel[i])
    bins[[chn]] <- append(bins[[chn]], func(2))	# 2 is close to 0 but safer
    gains[[chn]] <- append(gains[[chn]], initialgains[i])
  }
  dev.off()
}


output <- vector()

# Create curve and function for each channel (multiple wells)
#for (i in 1:(length(channels))) {
i <- 1
bins_c <- bins[[i]]
gains_c <- gains[[i]]



# Remove values not making a upward trend (Martin Hjelmare)
point.connected <- 0
point.start <- 1
point.end <- 1
for (k in 1:(length(bins_c)-1)) {
  for (l in (k+1):length(bins_c)) {
    print(bins_c[l-1])
    if (bins_c[l] >= bins_c[l-1]) {
      if ((l-k+1) > point.connected) {
        point.connected <- l-k+1
        point.start <- k
        point.end <- l
      }
    }
    else {
      break
    }
  }
}
print(point.connected)
bins_c <- bins_c[point.start:point.end]
gains_c <- gains_c[point.start:point.end]
gain[[i]] <- round(initialgains[channels[i]])

# HAVE TO ADD CHANGABLE NLS FUNCTION AND STARTING VALUES AFTER THE ON/OFF SWITCH TO MAKE IT WORK
# Switch to change axis for plots and regressions
#if (onOff == "gain.bin") {
#  x <- gains_c
#  y <- bins_c
#  output[i] <- round(binmax)
#}
#if (onOff == "bin.gain") {
#  x <- bins_c
#  y <- gains_c
#  output[i] <- round(gain[[i]])
#}

plot(gains_c, bins_c)

#if (length(bins_c) >= 3) {
if (length(bins_c) >= 3) {
  # Fit curve
  sink("/dev/null")	# Suppress output
  #if (onOff == "gain.bin") {
    curv2 <- tryCatch(nls(bins_c ~ C*gains_c^D, start=list(C=-1, D=5), trace=T), warning=function(e) NULL, error=function(e) NULL)
  #}
  #if (onOff == "bin.gain") {
  #  curv2 <- tryCatch(nls(y ~ C*x^D, start=list(C=1, D=1), trace=T), warning=function(e) NULL, error=function(e) NULL)
  #}
  sink()
  # Find function
  if (!is.null(curv2)) {
    func2 <- function(val, A=coef(curv2)[1], B=coef(curv2)[2]) {A*val^B}
    lines(gains_c, fitted.values(curv2), lwd=2, col="green")
    abline(v=binmax)
    #testing
    print(paste("i:",i))
    # Enter gain values from previous gain screening with first
    # objective into function func2
    output[i] <- round(func2(inputGain[i]))
  }
}



# Use func3 to get output from first objective which will be input for second objective in func3 next round
#testing
#print("firstObj")
#inputSecObj <- func3(firstInitialgainsCSV, inputGain, firstObjWorkPath, firstObjHistoBase, "gain.bin")
#testing
#print("secObj")
#outputSecObj <- func3(secInitialgainsCSV, inputSecObj, secObjWorkPath, secObjHistoBase, "bin.gain")

#cat(paste(outputSecObj[1], outputSecObj[2], outputSecObj[3], outputSecObj[4]))