'''
Created on 30 Jan 2021
@author: ethancollopy
'''

import requests
import csv
import ast
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as tick

import datetime

def display(output_array):
    for line in output_array :
        print (" output: %s " % ( line ))
 
def saveResponseData(fileName, response ):
    write_file = (targetfile)
    with open(write_file, 'w') as f:
        writer = csv.writer(f, delimiter=' ', lineterminator='\n')
        writer.writerows(response.text.splitlines())
 
def removeQuotesFromArrayItems(input_array):       
    output_array = []
    for line in input_array :        
        itemLine = line.split(",")
        #size = len(line.split(","))
        output_item = []
        for item in itemLine:
            output_item.append( item.replace('"','') )
        output_array.append(output_item)    

    return output_array

def getUrlResponse(regionCode, metricType ):
    query = {'areaType':'region','areaCode':regionCode,'metric':metricType,'format':'csv' }
    response = requests.get('https://api.coronavirus.data.gov.uk/v2/data', params=query )
    #response = requests.get('http://www.google.com', params=query)
    output_array = removeQuotesFromArrayItems(response.text.splitlines())
    npArray = np.array(output_array)
    print(output_array)
    npArray2 = np.delete(npArray, 0, axis=1)
    newDataFrame = pd.DataFrame( npArray2,    # values
             index=npArray[:,[0]],     # 1st column as index
             columns= ['areaType','areaCode','areaName', metricType ]   )
    newDataFrame.index = newDataFrame.index.map("".join)
    newDataFrame = newDataFrame.drop(['date'])
    return (newDataFrame,response)


def getFileResponse(regionName, metric):
    #responseFileName = "data/" + str(regionName) + "_" + str(metric) + "Data.csv" 
    responseFileName = "data/" + str(regionName) + "Data.csv" 
    responseDF = pd.read_csv( responseFileName ) 
   # responseDF = pd.read_csv("data/%s_%sData.csv" % regionName %metric) 
    responseDF.columns = responseDF.columns.str.replace(' ', '') # remove spaces from column names
    for i, cols in enumerate(responseDF.columns):
        responseDF.iloc[:, i] = responseDF.iloc[:, i].str.replace('"', '')  
        responseDF.iloc[:, i] = responseDF.iloc[:, i].str.replace(' ', '')  
    responseDF =  responseDF.set_index('date')      
    return responseDF

def turnCumulativeIntoDiffColumn(newDataFrame, metricType, regionTitle ):
    if metricType == 'cumDeaths28DaysByDeathDate':
        newDataFrame['diff'] = newDataFrame[metricType].diff(-1)
        newDataFrame = newDataFrame.drop(columns=[metricType])
        newDataFrame = newDataFrame.rename(columns={ "diff": regionTitle })
        return newDataFrame
    else:
        newDataFrame = newDataFrame.rename(columns={ metricType: regionTitle })
        return newDataFrame
        

def populateDataframe( newDataFrame , metricType ):
    if  metricType == 'cumDeaths28DaysByDeathDate':
        newDataFrame = newDataFrame.sort_index(ascending=False)
    newRegionTitle = str(newDataFrame['areaName'][0]).replace(" ","")
    newDataFrame = newDataFrame.drop(columns=['areaType','areaCode','areaName'])
    newDataFrame[[metricType ]] = newDataFrame[[metricType]].apply(pd.to_numeric)
    newDataFrame = turnCumulativeIntoDiffColumn(newDataFrame, metricType, newRegionTitle )
    return newDataFrame


def mergeDataFrame(dataframeRegion_Dict,regions):
    finalDataframe = pd.DataFrame()
    for region in regions:
        outputDf = dataframeRegion_Dict[region[0]]
        finalDataframe = pd.merge(finalDataframe, outputDf, left_index=True, right_index=True, how='outer')
    return finalDataframe


def formatPlot(ax,date,metricName):
    if metricName == 'cumDeaths28DaysByDeathDate':
        ax.set_title(" UK COVID-19 Daily Deaths by Region as of %s" % date)
        ax.set_ylabel('Number of Deaths')   
    else:
        ax.set_title(" UK COVID-19 Daily Cases by Region as of %s" % date)
        ax.set_ylabel('Number of Cases')   
    ax.set_xlabel('Date')   
    ax.grid(True)
    ax.set_facecolor('gainsboro')
    ax.tick_params(labelsize=8)
        
#--------------------------------------------------------
# BEGIN CODE
#--------------------------------------------------------        
        
today = datetime.date.today()
print(today)
metricName = 'cumDeaths28DaysByDeathDate'
#metricName = 'newCasesByPublishDate'

regions = [ ("london","E12000007"), ("southwest","E12000009"), ("eastmidlands","E12000004") , 
("NorthWest" , "E12000002" ) , ("YorksHum" , "E12000003" ) , ( "SouthEast" , "E12000008"  ) , 
("NorthEast" , "E12000001" ) , ("EastOfEngland" , "E12000006"  ) , ("WestMidlands" , "E12000005" ) ]

dataframeRegion_Dict = {} 

for region in regions:
    (response,responseOriginal) = getUrlResponse(region[1], metricName )
   # response = getFileResponse(region[0],metricName)
    df = populateDataframe(response, metricName )
    
    dataframeRegion_Dict[region[0]] = df
    print('save file')
    saveFileName = str(region[0]) + "_" + str(metricName) + ".csv"
    #targetfile = "/Users/ethancollopy/git/pythonPlotting/python.datascience.views/src/data/{}_{}Data.csv".format(region[0],metricName)   
    targetfile = "/Users/ethancollopy/git/pythonPlotting/python.datascience.views/src/data/{}".format(saveFileName)   
    saveResponseData(targetfile, responseOriginal)
    
print(dataframeRegion_Dict.keys())

finalDataframe = mergeDataFrame(dataframeRegion_Dict, regions)

#print(finalDataframe.loc[['2021-01-10']].sum(axis = 1))

print(finalDataframe.count)
#finalDataframe = finalDataframe.drop(finalDataframe.head(40).index,inplace=True) # drop last n rows
#finalDataframe = finalDataframe.iloc[70:]
#finalDataframe = finalDataframe.drop(finalDataframe.index[[0,200]])

print(finalDataframe.count)
#finalDataframe.drop(finalDataframe.tail(3).index,inplace=True) # drop last n rows

ax = finalDataframe.plot(linewidth = "0.8")
formatPlot( ax, today , metricName)

#plt.figure(figsize=(11.69,8.27))
if metricName == 'cumDeaths28DaysByDeathDate':
    plt.savefig("charts/UKDeaths_%s.pdf" % today , dpi=300 )
    
if metricName == 'newCasesByPublishDate':
    plt.savefig("charts/UKCases_%s.pdf" % today , dpi=300 )
    
plt.show()

                                                                                     
        
    
