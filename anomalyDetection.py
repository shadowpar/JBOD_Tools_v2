#!/usr/bin/python3


from hancockStorageMonitor.localgatherers.storage_info import storage_info
import statistics
from pprint import pprint

attrStats = {}

info = storage_info()

responseTimes = []
outliers = {}
statsToCompare = ['readerrorcorrectedbyreadwrite','readerrorcorrectedeccdelayed','readerrorcorrectedeccfast','readerrorcorrectedtotal',
'readerroruncorrectedtotal','responsetime','growndefects','temperature','verifyerrorcorrectedbyreadwrite',
'verifyerrorcorrectedeccdelayed','verifyerrorcorrectedeccfast','verifyerrorcorrectedtotal','verifyerroruncorrectedtotal',
'writeerrorcorrectedbyreadwrite','writeerrorcorrectedeccdelayed','writeerrorcorrectedeccfast','writeerrorcorrectedtotal','writeerroruncorrectedtotal']

statsThreshhold = {'readerrorcorrectedbyreadwrite':None,'readerrorcorrectedeccdelayed':None,'readerrorcorrectedeccfast':None,'readerrorcorrectedtotal':None,
'readerroruncorrectedtotal':1,'responsetime':0.5,'growndefects':1,'temperature':30,'verifyerrorcorrectedbyreadwrite':None,
'verifyerrorcorrectedeccdelayed':None,'verifyerrorcorrectedeccfast':None,'verifyerrorcorrectedtotal':None,'verifyerroruncorrectedtotal':1,
'writeerrorcorrectedbyreadwrite':None,'writeerrorcorrectedeccdelayed':None,'writeerrorcorrectedeccfast':None,'writeerrorcorrectedtotal':None,'writeerroruncorrectedtotal':1}
#script only designed for use with single chassis setups.
chassisSerial = list(info.harddrivesByChassis.keys())[0]
for diskSerial in info.harddrivesByChassis[chassisSerial]:
    for attr in statsToCompare:
        if attr not in attrStats:
            attrStats[attr] = {'mean':0,'stdev':0,'items':[]}
        attrvalue = info.harddrivesByChassis[chassisSerial][diskSerial].attributes[attr]
        attrStats[attr]['items'].append(attrvalue)



for attr in attrStats:
    attrStats[attr]['mean'] = statistics.mean(attrStats[attr]['items'])
    attrStats[attr]['stdev'] = statistics.stdev(attrStats[attr]['items'])
    print("-------------------------------------------------------")
    print("The mean ",attr,"is ",str(attrStats[attr]['mean']))
    print("The standard deviation of ",attr,"is ",str(attrStats[attr]['stdev']))
    print("-------------------------------------------------------")

for diskSerial in info.harddrivesByChassis[chassisSerial]:
    for attr in attrStats:
        attrvalue = info.harddrivesByChassis[chassisSerial][diskSerial].attributes[attr]
        # Check against normal value threshhold if there is one.
        if statsThreshhold[attr] is not None and attrvalue < statsThreshhold[attr]:
            continue
        delta = abs(float(attrvalue) - float(attrStats[attr]['mean']))
        if delta > (3*float(attrStats[attr]['stdev'])):
            # print("Disk with serial number",diskSerial,"has an abnormal",attr,"value.")
            if not diskSerial in outliers:
                outliers[diskSerial] = {attr:{'value':str(attrvalue),'delta':str(delta)}}
            else:
                outliers[diskSerial][attr] = {'value':str(attrvalue),'delta':str(delta)}

print("The outliers are:")
print("-------------------------")
for serial in outliers:
    print("Disk ",info.harddrivesByChassis[chassisSerial][serial].attributes['children'],"have following anomalies")
    pprint(outliers[serial])

