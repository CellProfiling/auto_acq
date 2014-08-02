first_obj_path <- "/home/martin/Skrivbord/test/std/10x/maxprojs/"
first_obj_base <- "/home/martin/Skrivbord/test/std/10x/maxprojs/U00--V00--"
first_init_gain_csv <- "/home/martin/Dev/auto_acq/gain.csv"
input_gain <- c(813,1004,910,756)
sec_obj_path <- "/home/martin/Skrivbord/test/std/40x/maxprojs/"
sec_obj_base <- "/home/martin/Skrivbord/test/std/40x/maxprojs/U00--V00--"
sec_init_gain_csv <- "/home/martin/Dev/auto_acq/gain2.csv"


setwd(first_obj_path)
filebase <- first_obj_base
# Initial gain values used
initialgains <- read.csv(first_init_gain_csv)$gain

input <- input_gain

gain <- list()
bins <- list()
gains <- list()

green <- 11;      # 11 images
blue <- 18;       # 7 images
yellow <- 25;     # 7 images
red <- 32;        # 7 images
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
  #png(filename=paste(filebase, "C", sprintf("%02d", i-1), ".ome.png", sep = ""))
  if (length(bin1) > 0) {
    plot(count1, bin1, log="xy")
  }
  # Fit curve
  sink("/dev/null")  # Suppress output
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
  #dev.off()
}

i <- 1

bins_c <- bins[[i]]
gains_c <- gains[[i]]

# Remove values not making a upward trend (Martin Hjelmare)
point.connected <- 0
point.start <- 1
point.end <- 1
for (k in 1:(length(bins_c)-1)) {
  for (l in (k+1):length(bins_c)) {
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
bins_c <- bins_c[point.start:point.end]
gains_c <- gains_c[point.start:point.end]
gain[[i]] <- round(initialgains[channels[i]])

x <- gains_c
y <- bins_c

plot(x, y)

curv2 <- nls(y ~ exp(C+x*D), start=list(C=10, D=0), trace=T)

func2 <- function(val, A=coef(curv2)[1], B=coef(curv2)[2]) {A*val^B}
lines(x, fitted.values(curv2), lwd=2, col="green")
abline(v=input[i])
