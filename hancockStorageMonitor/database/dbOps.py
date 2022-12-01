from hancockStorageMonitor.database.sqlalchemy_classes import headnode, jbod, harddrive, logicaldisk, cpu, raidarray
from hancockStorageMonitor.common.staticdatacentral import DBSEARCHKEYS
from pathlib import Path
from pprint import pformat

dbOpsErrors = Path('/var').joinpath('log').joinpath('storageMonitor').joinpath('dbOps.log')

cpuTranslate = {'model': 'model', 'architecture': 'architecture', 'bogomips': 'bogomips', 'byteorder': 'byteorder',
                'numcores': 'numcores', 'cpufreqmhz': 'cpufreqmhz', 'opmodes': 'opmodes', 'l1dcache': 'l1dcache',
                'l1icache': 'l1icache', 'l2cache': 'l2cache', 'l3cache': 'l3cache',
                'threadspercore': 'threadspercore', 'vendor': 'vendor', 'virtualization': 'virtualization',
                'modified': 'modified'}

headnodeTranslate = {'name': 'name', 'cpu': 'cpuid', 'model': 'model', 'datacenter': 'datacenter', 'rack': 'rack',
                     'slot': 'slot', 'experiment': 'experiment', 'numsockets': 'numsockets',
                     'numtotalthreads': 'numtotalthreads',
                     'modified': 'modified','serialnumber':'serialnumber','raidtype':'raidtype'}

harddriveTranslate = {'headnode': 'headnodeid', 'serialnumber': 'serialnumber', 'index': 'index', 'slot': 'slot',
                      'jbod': 'jbodid', 'raidarray': 'raidarrayid', 'vendor': 'vendor',
                      'model': 'model', 'firmware': 'firmware', 'temperature': 'temperature',
                      'smartstatus': 'smartstatus', 'growndefects': 'growndefects', 'rotationrate': 'rotationrate',
                      'capacity': 'capacity', 'protocol': 'protocol', 'health': 'health',
                      'indicatorled': 'indicatorled', 'readerrorcorrectedtotal': 'readerrorcorrectedtotal',
                      'readerroruncorrectedtotal': 'readerroruncorrectedtotal',
                      'readerrorcorrectedbyreadwrite': 'readerrorcorrectedbyreadwrite',
                      'readerrorcorrectedeccfast': 'readerrorcorrectedeccfast',
                      'readerrorcorrectedeccdelayed': 'readerrorcorrectedeccdelayed',
                      'verifyerrorcorrectedtotal': 'verifyerrorcorrectedtotal',
                      'verifyerroruncorrectedtotal': 'verifyerroruncorrectedtotal',
                      'verifyerrorcorrectedbyreadwrite': 'verifyerrorcorrectedbyreadwrite',
                      'verifyerrorcorrectedeccfast': 'verifyerrorcorrectedeccfast',
                      'verifyerrorcorrectedeccdelayed': 'verifyerrorcorrectedeccdelayed',
                      'writeerrorcorrectedtotal': 'writeerrorcorrectedtotal',
                      'writeerroruncorrectedtotal': 'writeerroruncorrectedtotal',
                      'writeerrorcorrectedbyreadwrite': 'writeerrorcorrectedbyreadwrite',
                      'writeerrorcorrectedeccfast': 'writeerrorcorrectedeccfast',
                      'writeerrorcorrectedeccdelayed': 'writeerrorcorrectedeccdelayed', 'modified': 'modified'}

logicalDiskTranslate = {'harddrive': 'harddriveid', 'iomodule': 'iomodule', 'name': 'name',
                        'sasaddress': 'sasaddress', 'scsiaddress': 'scsiaddr', 'serialnumber': 'serialnumber',
                        'modified': 'modified'}

raidArrayTranslate = {'headnode': 'headnodeid', 'name': 'name', 'uuid': 'uuid', 'chunksize': 'chunksize',
                      'componentsize': 'componentsize', 'degraded': 'degraded', 'totalnumdisks': 'totalnumdisks',
                      'lastsyncaction': 'lastsyncaction', 'mismatchcnt': 'mismatchcnt', 'syncspeed': 'syncspeed',
                      'syncspeedmax': 'syncspeedmax', 'syncspeedmin': 'syncspeedmin', 'syncaction': 'syncaction',
                      'stripecachesize': 'stripecachesize', 'raidlevel': 'raidlevel',
                      'consistencypolicy': 'consistencypolicy', 'arraystate': 'arraystate',
                      'metadataversion': 'metadataversion',
                      'major': 'major', 'minor': 'minor', 'mountpoint': 'mountpoint', 'filesystem': 'filesystem',
                      'bitmapfile': 'bitmapfile', 'modified': 'modified'}

jbodTranslate = {'headnode': 'headnodeid', 'vendor': 'vendor', 'model': 'model', 'serialnumber': 'serialnumber',
                 'health': 'health', 'datacenter': 'datacenter', 'rack': 'rack', 'slot': 'slot',
                 'numslots': 'numslots',
                 'logicalid': 'logicalid', 'managementipa': 'managementipa',
                 'managementstatusa': 'managementstatusa', 'managementmaca': 'managementmaca',
                 'managementipb': 'managementipb',
                 'managementstatusb': 'managementstatusb', 'managementmacb': 'managementmacb',
                 'modified': 'modified'}

transTypes = {cpu: cpuTranslate, headnode: headnodeTranslate, harddrive: harddriveTranslate,
              raidarray: raidArrayTranslate, logicaldisk: logicalDiskTranslate, jbod: jbodTranslate}

def clearDB(sessionObj):
    targets = [logicaldisk,harddrive,raidarray,jbod,headnode,cpu]
    for rcdtype in targets:
        rcds = sessionObj.query(rcdtype)
        rcds.delete()
        sessionObj.commit()



def mass_db_insert(sessionObj,
                   newDbObjs):  # a generalized function for mass insertion of different table elements into the database.
    searchKey = DBSEARCHKEYS[type(newDbObjs[0])]  # Gives the items that uniquely identify a record
    dbRecords = sessionObj.query(type(newDbObjs[0]))  # returns all the records of a certain type
    detectedObjs = {}  # maps unique attributes to potential new db objects
    updatedObjs = []  # a list of existing records that has been updated and doesnt need to be added before commit.
    for newDbObj in newDbObjs:
        if type(searchKey) == tuple:
            newDbKey = tuple(getattr(newDbObj, tuplet) for tuplet in searchKey)
        elif type(searchKey) == str:
            newDbKey = getattr(newDbObj, searchKey)
        else:
            newDbKey = getattr(newDbObj, str(searchKey))
        detectedObjs[newDbKey] = newDbObj
    for dbRecord in dbRecords:
        if type(searchKey) == tuple:
            currentDbKey = tuple(getattr(dbRecord, tuplet) for tuplet in searchKey)
        elif type(searchKey) == str:
            currentDbKey = getattr(dbRecord, searchKey)
        else:
            currentDbKey = getattr(dbRecord, str(searchKey))
        if currentDbKey in detectedObjs:
            for attr in detectedObjs[
                currentDbKey].__dict__:  # iterate through the properties of cpu class and update the database records.
                # being careful not to messs with the state variable for cpu class or the 'id' field
                if attr not in ['id'] and '_' not in attr:
                    newValue = getattr(detectedObjs[currentDbKey], attr)
                    setattr(dbRecord, attr, newValue)
            updatedObjs.append(currentDbKey)
    for newDbKey in detectedObjs:
        if newDbKey not in updatedObjs:
            sessionObj.add(detectedObjs[newDbKey])
    sessionObj.commit()


def translateAndCreate(currObj, transType, auxData={}):  # certain db record types have references to other types of records. auxData provides this
    # Here we are adding the auxiliary data from the existing records to the new database objects.
    try:
        currObj['cpuid'] = currObj['headnodeid'] = currObj['jbodid'] = currObj['raidarrayid'] = None
        if transType == headnode:  # This bit handles the referential integrity constraints between tables for existing entries that are updated.
            currObj['cpuid'] = auxData[cpu][currObj['cpumodel']]
        elif transType == raidarray or transType == jbod:
            currObj['headnodeid'] = auxData[headnode][currObj['hostname']]
        elif transType == harddrive:
            currObj['headnodeid'] = auxData[headnode][currObj['hostname']]
            currObj['jbodid'] = auxData[jbod][currObj['chassisSerial']]
            try:
                currObj['raidarrayid'] = auxData[raidarray][currObj['mdparent']]
            except KeyError:
                currObj['raidarrayid'] = None
        elif transType == logicaldisk:
            currObj['harddriveid'] = auxData[harddrive][currObj['serialnumber']]
        # Each translate dictionary maps the property names from serialized data to the appropriate property names for the associated database objects.
        kwargs = {}
        for key in transTypes[transType]:
            value = transTypes[transType][key]
            kwargs[key] = currObj[value]
        dbobject = transType(**kwargs)
        return dbobject
    except Exception as e:
        with dbOpsErrors.open('a') as f:
            f.write("There is a problem in dbobps with following arguments")
            f.write('currentObject=')
            f.write(pformat(currObj))
            f.write('transtype=')
            f.write(str(transType))
            f.write(str(e))
        print(e)
        return None