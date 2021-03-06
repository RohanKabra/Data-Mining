import sys
import os
import re
from nltk.corpus import stopwords
from nltk.stem.porter import *
from bisect import *
import collections
import numpy as np
import time
import cPickle as pickle
import decimal

#
# Pre-Process Part
#

# Set fraction size and prefix path
# File Fraction size to Read. Set between 0.1 and 1
fileFractionSize = 1
fileTestFractionSize = 1
prefixPath = "./dataset/Reuters21578-Apte-115Cat/"
# prefixPath = "./dataset/20news-bydate/"
# prefixPath = "./dataset/ohsumed-first-20000-docs/"

# Parameter : #1 - fraction size. #2 - dataSet
# Example: python project_save.py 1 ./dataset/Reuters21578-Apte-115Cat/

# Set FractionSize and Data Set to Use
if len(sys.argv) >= 2:
    if float(sys.argv[1]) > 0 and float(sys.argv[1]) <= 1:
        fileTestFractionSize = sys.argv[1]

if len(sys.argv) == 3:
    prefixPath = sys.argv[2]

startTime = time.time()
print "Starting...\n"


# Identify Category
dataSet = prefixPath.split('/')[2]
print "Data Set to be used:\t" + dataSet
categoryList =  os.listdir(prefixPath + "training/")
categoryTestList = os.listdir(prefixPath + "test/")

# StopWord Definition
stopwordsList = stopwords.words('english')
stemmer = PorterStemmer()
fileNum = 0
fileTestNum = 0
categoryNum = 0
categoryTestNum = 0
outputFile = open('pre_processed_data_object_tfidf_' + dataSet + "_" + str(fileTestFractionSize), 'wb')
filesToTrainAndTest = 10

# File Fraction size to Read. Set between 0.1 and 1
fileFractionSize = decimal.Decimal(fileFractionSize,1)
fileTestFractionSize = decimal.Decimal(fileTestFractionSize,1)
print "Fraction to be used:\t" + str(fileTestFractionSize)

# Define Regular Expression to pre-process strings. Only AlphaNumeric and whitespace will be kept.
strPattern = re.compile('[^a-zA-Z0-9 ]')

# A dictionary which keeps token and its frequency for each category. It will keep a Dictionary in a Dictionary.
# key - category, value-{'term':frequency}
# Example : {'acq' : {'hi':1,'compu':3,'move':1 ...}}
categoryAlphaNumericStrStemmedDict = {}
categoryTestAlphaNumericStrStemmedDict = {}

# A dictionary which keeps token and its frequency for each file in each category for TEST set
# {category : { file : {term : frequency ...}}}
# Example : {acq : { 000056 : {'hi' : 1 , 'compu' : 3 ...}}}
categoryTestAllFileAlphaNumericStrStemmedDict = {}

# A dictionary which keeps token, its frequency, and category for each file. It is layered Dictionary structure.
# 1st layer Dict {A}: key - category, value-{'term':frequency}
# 2nd layer Dict {B}: key - filename, value-{A}
# Example : {'000056' : {'acq' : {'hi':1, 'compu:3, 'move':1 ...}}}
fileAlphaNumericStrStemmedDict = {}
fileTestAlphaNumericStrStemmedDict = {}

# A dictionary which keeps test filename, and its categories in Set
# {'000056' : ('acq', 'alum')}
fileTestBelongCategory = {}
fileBelongCategory = {}

# A list which keeps whole vocabularies throughout whole categories. It will be sorted.
# Example : ['current', 'curtail', 'custom', 'cut', 'cuurent', 'cvg', 'cwt', 'cypru', 'cyrpu', 'd', 'daili' ...]
wholeVocabularySet = set()
wholeVocabularyList = []
wholeTestVocabularySet = set()
wholeTestVocabularyList = []

wholeVocabularyFrequency = 0
wholeTestVocabularyFrequency = 0

# A dictionary which keeps entire vocabulary and its frequency across whole categories
# Example : {'current' : 110, 'said' : 10000 ...... }
wholeVocabularyFrequencyDict = {}
wholeVocabularyTestFrequencyDict = {}

# A dictionary which keeps number of files in each category
# Example : {'acq': 115, 'alum': 222 ...}
numberOfFilesInEachCategoryDict = {} 
numberOfFilesInEachCategoryTestDict = {} 

# A dictionary which keeps fraction of [number of files in each category] / [number of entire files]
# Example : {'acq':0.015, 'alum':0.031 ...}
fractionOfFilesInEachCategoryDict = {} 
fractionOfFilesInEachCategoryTestDict = {} 


# Read Training Data Set
print "\nReading Training data Set"
print "Elap(s)\Dur(s)\tCategory#\tName\t#ofFile\t#ofUniqueTerms\t#Frequency"

#Iterate each category and create vector space for each category
for category in categoryList:

    tmpTime = time.time()

    # Temporary code to reduce time to process. Eliminate when processing entire set

    # if category == 'acq' or category == '.DS_Store':
    #     continue
    # if categoryNum == filesToTrainAndTest:
    #     break

    fileInCategoryList = os.listdir(prefixPath + "training/" + category + "/")
    tmpCategoryAlphaNumericStrStemmedDict = {}
    # categoryAlphaNumericStrStemmedDict[categoryNum][0] = category
    # categoryTmpColumn = {}
    # categoryTmpColumn.append(str(category))
    tmpFileNum = 0
    tmpFreqPerCategory = 0
    tmpNumberOfUniqueTermPerCategory = 0
    tmpNumberOfTermPerCategory = 0

    for fileToTrain in fileInCategoryList:
        fileToTrainPath = prefixPath + 'training/' + category + '/' + fileToTrain

        # Check the file size and read some fraction of the file defined in "fileFractionSize" variable
        filesize = os.path.getsize(fileToTrainPath)
        chunkReadSize = int(round(filesize * fileFractionSize))
        f = open(fileToTrainPath)
        fileStr = f.read(chunkReadSize)
        fileTmpColumn = {}
        fileTmpColumn1 = {}
        # fileTmpColumn.append(str(category))
        # fileTmpColumn.append(str(fileToTrain))

        # Remove non alphanumeric characters in the chunk
        fileAlphaNumericStr = re.sub(strPattern, ' ', fileStr)

        # Convert to lower case
        fileAlphaNumericStr = fileAlphaNumericStr.lower()

        # Remove Stop Words and Tokenize the chunk into a List by using whitespace
        fileAlphaNumericStrNoStopWords = ' '.join([word for word in fileAlphaNumericStr.split() if word not in stopwordsList])
        # fileAlphaNumericStrNoStopWords = ' '.join([word for word in fileAlphaNumericStr.split()])
        fileAlphaNumericStrList = fileAlphaNumericStrNoStopWords.split()
#         fileAlphaNumericStrList = fileAlphaNumericStr.split()

        # Apply Porter Stemmer and Put token and frequency to One Dict
        tmpFileAlphaNumericStrStemmedDict = {}

        # Create vector space (Dict) for each category
        for words in fileAlphaNumericStrList:
            tmp = stemmer.stem(words)
            # tmp = words
            tmp1 = tmpFileAlphaNumericStrStemmedDict.get(tmp)
            tmp2 = tmpCategoryAlphaNumericStrStemmedDict.get(tmp)
            if tmp1 == None:
                tmpFileAlphaNumericStrStemmedDict[tmp] = 1
            else:
                tmpFileAlphaNumericStrStemmedDict[tmp] = tmp1 + 1
            if tmp2 == None:
                tmpCategoryAlphaNumericStrStemmedDict[tmp] = 1
            else:
                tmpCategoryAlphaNumericStrStemmedDict[tmp] = tmp2 + 1
            tmpFreqPerCategory += 1
            if tmp not in wholeVocabularySet:
                wholeVocabularySet.add(tmp)

        fileTmpColumn1[category] = tmpFileAlphaNumericStrStemmedDict
        # fileTmpColumn.append(tmpFileAlphaNumericStrStemmedDict)
        # fileTmpColumn[str(fileToTrain)] = fileTmpColumn1
        fileNum += 1
        tmpFileNum += 1
        if fileToTrain in fileAlphaNumericStrStemmedDict:
            fileBelongCategory[fileToTrain].append(category)
        else:
            tmp = []
            tmp.append(category)
            fileBelongCategory[fileToTrain] = tmp

        fileAlphaNumericStrStemmedDict[fileToTrain] = fileTmpColumn1

    # categoryTmpColumn.append(tmpCategoryAlphaNumericStrStemmedDict)
    categoryAlphaNumericStrStemmedDict[category] = tmpCategoryAlphaNumericStrStemmedDict
    categoryNum += 1
    wholeVocabularyFrequency += tmpFreqPerCategory
    numberOfFilesInEachCategoryDict[category] = tmpFileNum

    print "%6.3g"%(time.time() - startTime) + "\t" + "%6.3g"%(time.time() - tmpTime) + "\t" + str(categoryNum) +  "\t" + category + "\t" + str(tmpFileNum) + "\t" + str(len(tmpCategoryAlphaNumericStrStemmedDict)) + "\t" + str(tmpFreqPerCategory)


print "\nReading Test data Set"
print "Elap(s)\Dur(s)\tCategory#\tName\t#ofFile\t#ofUniqueTerms\t#Frequency"

#Iterate each TEST category and create vector space for each category
for categoryTest in categoryTestList:

    tmpTime = time.time()

    # Temporary code to reduce time to process. Eliminate when processing entire set


    fileInCategoryTestList = os.listdir(prefixPath + "test/" + categoryTest + "/")
    tmpCategoryTestAlphaNumericStrStemmedDict = {}
    # categoryAlphaNumericStrStemmedDict[categoryNum][0] = category
    # categoryTestTmpColumn = []
    # categoryTestTmpColumn.append(str(categoryTest))
    tmpFileTestNum = 0
    tmpFreqPerCategoryTest= 0
    tmpNumberOfUniqueTermPerCategoryTest = 0
    tmpNumberOfTermPerCategoryTest = 0

    for fileToTest in fileInCategoryTestList:
        fileToTestPath = prefixPath + 'test/' + categoryTest + '/' + fileToTest

        # Check the file size and read some fraction of the file defined in "fileFractionSize" variable
        filesizeTest = os.path.getsize(fileToTestPath)
        chunkTestReadSize = int(round(filesizeTest * fileTestFractionSize))
        f = open(fileToTestPath)
        fileTestStr = f.read(chunkTestReadSize)
        fileTestTmpColumn = {}
        # fileTestTmp1Column = {}

        # fileTestTmpColumn.append(str(categoryTest))
        # fileTestTmpColumn.append(str(fileToTest))

        # Remove non alphanumeric characters in the chunk
        fileTestAlphaNumericStr = re.sub(strPattern, ' ', fileTestStr)

        # Convert to lower case
        fileTestAlphaNumericStr = fileTestAlphaNumericStr.lower()

        # Remove Stop Words and Tokenize the chunk into a List by using whitespace
        fileTestAlphaNumericStrNoStopWords = ' '.join([word for word in fileTestAlphaNumericStr.split() if word not in stopwordsList])
        # fileTestAlphaNumericStrNoStopWords = ' '.join([word for word in fileTestAlphaNumericStr.split()])
        fileTestAlphaNumericStrList = fileTestAlphaNumericStrNoStopWords.split()

        # Apply Porter Stemmer and Put token and frequency to One Dict
        tmpFileTestAlphaNumericStrStemmedDict = {}

        # Create vector space (Dict) for each category
        for words in fileTestAlphaNumericStrList:
            tmp = stemmer.stem(words)
            # tmp = words
            if tmpFileTestAlphaNumericStrStemmedDict.get(tmp) == None:
                tmpFileTestAlphaNumericStrStemmedDict[tmp] = 1
            else:
                tmpFileTestAlphaNumericStrStemmedDict[tmp] += 1
            if tmpCategoryTestAlphaNumericStrStemmedDict.get(tmp) == None:
                tmpCategoryTestAlphaNumericStrStemmedDict[tmp] = 1
            else:
                tmpCategoryTestAlphaNumericStrStemmedDict[tmp] += 1
            tmpFreqPerCategoryTest += 1
            if tmp not in wholeTestVocabularySet:
                wholeTestVocabularySet.add(tmp)

        fileTestTmpColumn[categoryTest] = tmpFileTestAlphaNumericStrStemmedDict
        # fileTestTmpColumn.append(tmpFileTestAlphaNumericStrStemmedDict)

        if fileToTest in fileTestAlphaNumericStrStemmedDict:
            fileTestBelongCategory[fileToTest].append(categoryTest)
        else:
            tmp = []
            tmp.append(categoryTest)
            fileTestBelongCategory[fileToTest] = tmp

        fileTestAlphaNumericStrStemmedDict[fileToTest] = fileTestTmpColumn

        # Put information to categoryTestAllFileAlphaNumericStrStemmedDict
        try:
            categoryTestAllFileAlphaNumericStrStemmedDict[categoryTest][fileToTest] = tmpFileTestAlphaNumericStrStemmedDict
        except KeyError:
            categoryTestAllFileAlphaNumericStrStemmedDict[categoryTest] = {fileToTest : tmpFileTestAlphaNumericStrStemmedDict}

        fileTestNum += 1
        tmpFileTestNum += 1

    # categoryTestTmpColumn.append(tmpCategoryTestAlphaNumericStrStemmedDict)
    categoryTestAlphaNumericStrStemmedDict[categoryTest] = tmpCategoryTestAlphaNumericStrStemmedDict
    categoryTestNum += 1
    wholeTestVocabularyFrequency += tmpFreqPerCategoryTest
    numberOfFilesInEachCategoryTestDict[categoryTest] = tmpFileTestNum

    print "%6.3g"%(time.time() - startTime) + "\t" + "%6.3g"%(time.time() - tmpTime) + "\t" + str(categoryTestNum) +  "\t" + categoryTest + "\t" + str(tmpFileTestNum) + "\t" + str(len(tmpCategoryTestAlphaNumericStrStemmedDict)) + "\t" + str(tmpFreqPerCategoryTest)


# Sort entire Vocabulary
wholeVocabularyList = list(wholeVocabularySet)
wholeVocabularyList.sort()

wholeTestVocabularyList = list(wholeTestVocabularySet)
wholeTestVocabularyList.sort()





print
print "Statistics of Entire Training data Set"
print "# of Categories:\t" + str(categoryNum)
print "# of Files:\t" + str(fileNum)
print "# of Vocabularies:\t" + str(len(wholeVocabularyList))
print "# of Frequency:\t" + str(wholeVocabularyFrequency)


# print
# print wholeVocabularyList

# for i in range(0,categoryNum):
#    print str(categoryAlphaNumericStrStemmedDict[i][0]) + " ::::::: " + str(categoryAlphaNumericStrStemmedDict[i][1])


# A two dimensional List which keeps frequency of term per category. 
# row = category. column = frequency of each term in that category.
# For term list, we are using whole terms across entire categories.
# Example : category- acq, bop, term- 'commonplac', 'commonwealth', 'commun'
#           commonplac   commonwealth  commun
#    acq         7              2         0
#    bop         8              9         1 
termFrequencyPerCategoryList = []

# Creating A two dimensional List which keeps frequency of term per category\
for key,value in categoryAlphaNumericStrStemmedDict.iteritems():
    tmpColumn = []
    tmpColumn.append(key)
    for term in wholeVocabularyList:
        # if len(tmpColumn) > 50:
        #     break
        tmp = value.get(term)
        if tmp == None:
            tmpColumn.append(0)
        else:
            tmpColumn.append(tmp)
    termFrequencyPerCategoryList.append(tmpColumn)

# Put frequency of each terms across entire categories
for key1, value1 in categoryAlphaNumericStrStemmedDict.iteritems():
    for key, value in value1.iteritems():
        try:
            wholeVocabularyFrequencyDict[key] = wholeVocabularyFrequencyDict[key] + value
        except KeyError:
            wholeVocabularyFrequencyDict[key] = value

# Put frequency of each terms across entire categories
for key1, value1 in categoryTestAlphaNumericStrStemmedDict.iteritems():
    for key, value in value1.iteritems():
        try:
            wholeVocabularyTestFrequencyDict[key] = wholeVocabularyTestFrequencyDict[key] + value
        except KeyError:
            wholeVocabularyTestFrequencyDict[key] = value

# for key1, value1 in fileAlphaNumericStrStemmedDict.iteritems():
#     for key,value in value1.iteritems():
#         print key + ":" + key1

# Calculate fractionOfFilesInEachCategoryDict
# for key1, value1 in fileAlphaNumericStrStemmedDict.iteritems():
#     for key, value in value1.iteritems():
#         tmp = numberOfFilesInEachCategoryDict.get(key)
#         if tmp == None:
#             numberOfFilesInEachCategoryDict[key] = 1
#         else:
#             numberOfFilesInEachCategoryDict[key] = tmp + 1

for key1, value1 in numberOfFilesInEachCategoryDict.iteritems():
    fractionOfFilesInEachCategoryDict[key1] = value1 / fileNum

# Calculate fractionOfFilesInEachCategoryTestDict
# for key1, value1 in fileTestAlphaNumericStrStemmedDict.iteritems():
#     for key, value in value1.iteritems():
#         tmp = numberOfFilesInEachCategoryTestDict.get(key)
#         if tmp == None:
#             numberOfFilesInEachCategoryTestDict[key] = 1
#         else:
#             numberOfFilesInEachCategoryTestDict[key] = tmp + 1

for key1, value1 in numberOfFilesInEachCategoryTestDict.iteritems():
    fractionOfFilesInEachCategoryTestDict[key1] = value1 / fileTestNum

# Entire Vocubulary List which include every terms from the training set and test set.
# wholeVocabularyFromTrainingAndTestSetList = []
wholeVocabularyFromTrainingAndTestSetList = list(set(wholeVocabularyList) | set(wholeTestVocabularyList))

# For entire vocabularies in the training set, create a dictionary that a list (value) which contains frequency per category (key)
# Orders of vocabularies are same for every list. The order is as same as that of in wholeVocabularyFromTrainingAndTestSetList.
# Example : { 'category' : '[frequency for 'said', frequency for 'mln' ...]', 'category' : '[frequency for 'said', frequency for 'mln' ...]'     
normalizedFrequencyPerCategoryInTrainingSetDict = {}
frequencyInFilePerCategoryInTrainingSetList = []
frequencyInFilePerCategoryInTestSetList = []

# Specify number of bins
numberOfBins = 5
frequencyInWordPerFileInTrainingSetList = []
frequencyInWordPerFileInTestSetList = []

# Helper function: 'Find rightmost value less than or equal to x in a'
# From http://docs.python.org/2/library/bisect.html#searching-sorted-lists
def find_le(a, x):
    i = bisect_right(a, x)
    if i:
        return i-1
    else:
        return -1

#
# Non-Sampling version of frequencyInFilePerCategoryInTrainingSetList
#

# # key = filename, value : {category : {term:frequency ...}}
# for key,value in fileAlphaNumericStrStemmedDict.iteritems():
#     
#     tmpList = []
#     
#     # key1 = category, value1 : {term:frequency... }
#     for key1, value1 in value.iteritems():
#         
#         for term in wholeVocabularyFromTrainingAndTestSetList:
#             
#             if term in value1:
#                 tmpList.append(value1[term])
#             else:
#                 tmpList.append(0)
#         
#         for idx in fileBelongCategory[key]:
#             tmpList1 = tmpList
#             tmpList1.append(idx)
#             
#             frequencyInFilePerCategoryInTrainingSetList.append(tmpList1)

#
# Sampling version of frequencyInFilePerCategoryInTrainingSetList
#

# # First, calculate term frequecy per each word across whole file
# for term in wholeVocabularyFromTrainingAndTestSetList:
# 
#     tmpList = []
#     
#     # key = filename, value : {category : {term:frequency ...}}
#     for key, value in fileAlphaNumericStrStemmedDict.iteritems():
# 
#         # key1 = category, value1 : {term:frequency... }
#         for key1, value1 in value.iteritems():
#             
#             # term is found
#             if term in value1:
#                 tmpList.append(value1[term])
#             else:
#                 tmpList.append(0)
#                 
#     minValue = min(tmpList)
#     maxValue = max(tmpList)
#     interval = 0.0
#     bins = []
#     # print
#     # print str(minValue) + ", " + str(maxValue) 
#     # print tmpList
#     
#     # If max value is zero, then we don't need to apply sampling since all value is zero
#     if maxValue == 0:
#         frequencyInWordPerFileInTrainingSetList.append(tmpList)
#     else:
#         interval = float((minValue + maxValue)) / numberOfBins
#         bins = np.arange(minValue,maxValue,interval)
#         for idx, val in enumerate(tmpList):
#             tmpVal = find_le(bins, val) * interval
#             tmpList[idx] = tmpVal
#         # print str(minValue) + ", " + str(maxValue) + ", " + str(interval) + ", " + str(len(tmpList)) + ", " + str(len(fileAlphaNumericStrStemmedDict)) + "," + str(bins)
#         # print tmpList
#         frequencyInWordPerFileInTrainingSetList.append(tmpList)    
# 
# tmpCount = 0
# 
# # Next, Reorganize the list per file, not per word
# for key, value in fileAlphaNumericStrStemmedDict.iteritems():
# 
#     tmpList = []
#     
#     for i in range(0,len(frequencyInWordPerFileInTrainingSetList)):
#         tmpList.append(frequencyInWordPerFileInTrainingSetList[i][tmpCount])
#         
#     for cat in fileBelongCategory[key]:
#         tmpList1 = tmpList
#         tmpList1.append(cat)
#         frequencyInFilePerCategoryInTrainingSetList.append(tmpList1)
#     
#     tmpCount += 1
# 
# del frequencyInWordPerFileInTrainingSetList


#
# Non-sampling version of frequencyInFilePerCategoryInTestSetList
#

# key = filename, value : {category : {term:frequency ...}}
# for key,value in fileTestAlphaNumericStrStemmedDict.iteritems():
#     
#     tmpList = []
#     
#     # key1 = category, value1 : {term:frequency... }
#     for key1, value1 in value.iteritems():
#         
#         for term in wholeVocabularyFromTrainingAndTestSetList:
#             
#             if term in value1:
#                 tmpList.append(value1[term])
#             else:
#                 tmpList.append(0)
#         
#         for idx in fileTestBelongCategory[key]:
#             tmpList1 = tmpList
#             tmpList1.append(idx)
#             
#             frequencyInFilePerCategoryInTestSetList.append(tmpList1)


#
# Sampling version of frequencyInFilePerCategoryInTestSetList
#

# # First, calculate term frequecy per each word across whole file
# for term in wholeVocabularyFromTrainingAndTestSetList:
# 
#     tmpList = []
#     
#     # key = filename, value : {category : {term:frequency ...}}
#     for key, value in fileTestAlphaNumericStrStemmedDict.iteritems():
# 
#         # key1 = category, value1 : {term:frequency... }
#         for key1, value1 in value.iteritems():
#             
#             # term is found
#             if term in value1:
#                 tmpList.append(value1[term])
#             else:
#                 tmpList.append(0)
#                 
#     minValue = min(tmpList)
#     maxValue = max(tmpList)
#     interval = 0.0
#     bins = []
#     # print
#     # print str(minValue) + ", " + str(maxValue) 
#     # print tmpList
#     
#     # If max value is zero, then we don't need to apply sampling since all value is zero
#     if maxValue == 0:
#         frequencyInWordPerFileInTestSetList.append(tmpList)
#     else:
#         interval = float((minValue + maxValue)) / numberOfBins
#         bins = np.arange(minValue,maxValue,interval)
#         for idx, val in enumerate(tmpList):
#             tmpVal = find_le(bins, val) * interval
#             tmpList[idx] = tmpVal
#         # print str(minValue) + ", " + str(maxValue) + ", " + str(interval) + ", " + str(len(tmpList)) + ", " + str(len(fileAlphaNumericStrStemmedDict)) + "," + str(bins)
#         # print tmpList
#         frequencyInWordPerFileInTestSetList.append(tmpList)    
# 
# tmpCount = 0
# 
# # Next, Reorganize the list per file, not per word
# for key, value in fileTestAlphaNumericStrStemmedDict.iteritems():
# 
#     tmpList = []
#     
#     for i in range(0,len(frequencyInWordPerFileInTestSetList)):
#         tmpList.append(frequencyInWordPerFileInTestSetList[i][tmpCount])
#         
#     for cat in fileTestBelongCategory[key]:
#         tmpList1 = tmpList
#         tmpList1.append(cat)
#         frequencyInFilePerCategoryInTestSetList.append(tmpList1)
#     
#     tmpCount += 1
# 
# del frequencyInWordPerFileInTestSetList


# # key : category, value : {term : frequency, term : frequency ...}}
# for key, value in categoryAlphaNumericStrStemmedDict.iteritems():
#   
#     tmpList = []
#       
#     for term in wholeVocabularyFromTrainingAndTestSetList:
#   
#         if term in value:
#             tmpList.append(value[term])
#         else:
#             tmpList.append(0)
#       
#     normalizedFrequencyPerCategoryInTrainingSetDict[key] = tmpList 
#   
#            
# # For entire vocabularies in the test set, create a dictionary that a list (value) which contains frequency per file (key)
# # Orders of vocabularies are same for every list. The order is as same as that of in wholeVocabularyFromTrainingAndTestSetList.
# # Example : { '0001268' : '[frequency for 'said', frequency for 'mln' ...]', 'category' : '[frequency for 'said', frequency for 'mln' ...]'     
# normalizedFrequencyPerTestFileDict = {}
#   
# # key : file, value : {category : {term : frequency, term : frequency ...}})
# for key, value in fileTestAlphaNumericStrStemmedDict.iteritems():
#   
#     #key1 : category, value1 : {term : frequency ...}
#     for key1, value1 in value.iteritems():
#         tmpList = []
#   
#         for term in wholeVocabularyFromTrainingAndTestSetList:
#       
#             if term in value1:
#                 tmpList.append(value1[term])
#             else:
#                 tmpList.append(0)
#       
#     normalizedFrequencyPerTestFileDict[key] = tmpList             

# for key,val in fileBelongCategory.iteritems():
#     print key + "\t" + str(len(val))

pickle.dump(fileFractionSize, outputFile, -1)
pickle.dump(fileTestFractionSize, outputFile, -1)
pickle.dump(categoryAlphaNumericStrStemmedDict, outputFile, -1)
pickle.dump(categoryTestAlphaNumericStrStemmedDict, outputFile, -1)
pickle.dump(categoryTestAllFileAlphaNumericStrStemmedDict, outputFile, -1)
pickle.dump(fileAlphaNumericStrStemmedDict, outputFile, -1)
pickle.dump(fileTestAlphaNumericStrStemmedDict, outputFile, -1)
pickle.dump(fileBelongCategory, outputFile, -1)
pickle.dump(fileTestBelongCategory, outputFile, -1)
# pickle.dump(normalizedFrequencyPerCategoryInTrainingSetDict, outputFile, -1)
# pickle.dump(normalizedFrequencyPerTestFileDict, outputFile, -1)
# pickle.dump(frequencyInFilePerCategoryInTrainingSetList, outputFile, -1)
# pickle.dump(frequencyInFilePerCategoryInTestSetList, outputFile, -1)
pickle.dump(wholeVocabularyFromTrainingAndTestSetList, outputFile, -1)
pickle.dump(wholeVocabularyList, outputFile, -1)
pickle.dump(wholeTestVocabularyList, outputFile, -1)
pickle.dump(wholeVocabularyFrequency, outputFile, -1)
pickle.dump(wholeTestVocabularyFrequency, outputFile, -1)
pickle.dump(wholeVocabularyFrequencyDict, outputFile, -1)
pickle.dump(wholeVocabularyTestFrequencyDict, outputFile, -1)
pickle.dump(numberOfFilesInEachCategoryDict, outputFile, -1)
pickle.dump(numberOfFilesInEachCategoryTestDict, outputFile, -1)
pickle.dump(fractionOfFilesInEachCategoryDict, outputFile, -1)
pickle.dump(fractionOfFilesInEachCategoryTestDict, outputFile, -1)
pickle.dump(categoryNum, outputFile, -1)
pickle.dump(fileNum, outputFile, -1)
pickle.dump(categoryTestNum, outputFile, -1)
pickle.dump(fileTestNum, outputFile, -1)
pickle.dump(termFrequencyPerCategoryList, outputFile, -1)

# print termFrequencyPerCategoryList

print "Done. Elapsed Time for pre-processing: " + str(time.time() - startTime)


# Now, print number of duplicated files
print "\nNumber of Unique Files:\t" + str(len(fileAlphaNumericStrStemmedDict))

numberOfTotalFile = 0
numberOfDuplicatedFile = 0
for key, val in fileBelongCategory.iteritems():
    if len(val) > 1:
        numberOfDuplicatedFile += 1
    numberOfTotalFile += len(val)

print "Number of All Files:\t" + str(numberOfTotalFile)
print "Number of Multi-Category Files:\t"+ str(numberOfDuplicatedFile)

print "Number of Unique Test Files:\t"+ str(len(fileTestAlphaNumericStrStemmedDict))

numberOfTotalTestFile = 0
numberOfDuplicatedTestFile = 0
for key, val in fileTestBelongCategory.iteritems():
    if len(val) > 1:
        numberOfDuplicatedTestFile += 1
    numberOfTotalTestFile += len(val)

print "Number of All Test Files:\t" + str(numberOfTotalTestFile)
print "Number of Multi-Category Test Files:\t"+ str(numberOfDuplicatedTestFile)




