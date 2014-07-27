# testing
#test <- commandArgs(TRUE)[1]

test <- "843 751 910 759"
print(test)
inputCharVectorList <- strsplit(test, " ")
inputGain <- inputCharVectorList[[1]]
print(inputGain[2])
print(inputGain[2]*2)
inputGain <- as.numeric(inputGain)
print(inputGain[2]*2)
