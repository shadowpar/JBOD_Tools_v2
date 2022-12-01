from hancockStorageMonitor.database.db_manager import db_manager
from pathlib import Path
from datetime import datetime, timedelta
from hancockStorageMonitor.database.sqlalchemy_classes import storageerror
from hancockStorageMonitor.common.staticdatacentral import PROCESSINGORDER
from hancockStorageMonitor.common.staticdatastorage import allhosts, CABLESPERJBOD, ERRORTYPES2SEVERITY
from pprint import pprint
import json

class dbaudit(object):
    def __init__(self,debug=False):
        self.debug = debug
        self.expectedHostRecords = []
        for expList in allhosts.values(): self.expectedHostRecords.extend(expList)
        self.dbManager = db_manager()
        self.errorLog = Path('/var').joinpath('log').joinpath('storageMonitor').joinpath('dbaudit.log')
        self.errorsByDevTypeID = {deviceType:{} for deviceType in PROCESSINGORDER}
        self.dbData = {tableType:self.dbManager.session.query(PROCESSINGORDER[tableType]) for tableType in PROCESSINGORDER}
        self.maps = idmapper(dbData=self.dbData)
        self.errorDataByType = {}
        self.overviewErrorData = {}
        self.detectedErrorTypes = []
        self.checkOldData()
        self.checkMissingData()
        self.checkSmartFailed()
        self.checkSASdiskNoArray()
        self.checkFailedSASpaths()
        self.checkFailedCables()
        self.dbManager.session.query(storageerror).delete()
        self.createStorageErrorDBs()
        self.buildOverviewData()
        self.dbManager.session_maker.close_all()
    def checkOldData(self):
        errorType = list(ERRORTYPES2SEVERITY.keys())[0]
        # severity = 2
        currentTime = datetime.utcnow()
        for record in self.dbData['headnodes']:
            modified = getattr(record,'modified')
            diff = currentTime-modified
            if diff > timedelta(minutes=8):
                if errorType not in self.detectedErrorTypes: self.detectedErrorTypes.append(errorType)
                theError = {'severity':ERRORTYPES2SEVERITY[errorType], 'description': 'The records for everything attached to this host are outdated by' + str(diff),
                            'errorType':errorType}
                if record.id not in  self.errorsByDevTypeID['headnodes'].keys():
                    self.errorsByDevTypeID['headnodes'][record.id] = [theError]
                else:
                    self.errorsByDevTypeID['headnodes'][record.id].append(theError)
    def checkMissingData(self):
        errorType = list(ERRORTYPES2SEVERITY.keys())[5]
        # severity = 2
        foundDBhosts = [getattr(record,'name') for record in self.dbData['headnodes']]
        diff = list(set(self.expectedHostRecords) - set(foundDBhosts))
        for item in diff:
            if errorType not in self.detectedErrorTypes: self.detectedErrorTypes.append(errorType)
            theError = {'severity':ERRORTYPES2SEVERITY[errorType], 'description': 'This server is not reporting any data.', 'errorType':errorType}
            if item not in self.errorsByDevTypeID['headnodes'].keys():
                self.errorsByDevTypeID['headnodes'][item] = [theError]
            else:
                self.errorsByDevTypeID['headnodes'][item].append(theError)
    def checkSmartFailed(self):
        errorType = list(ERRORTYPES2SEVERITY.keys())[1]
        for disk in self.dbData['harddrives']:
            if getattr(disk,'smartstatus') != 'passed':
                if errorType not in self.detectedErrorTypes: self.detectedErrorTypes.append(errorType)
                theError = {'severity':ERRORTYPES2SEVERITY[errorType], 'description': 'This disk has a failed smart status:' + str(disk.smartstatus),
                            'errorType':errorType}
                if disk.id not in self.errorsByDevTypeID['harddrives'].keys():
                    self.errorsByDevTypeID['harddrives'][disk.id] = [theError]
                else:
                    self.errorsByDevTypeID['harddrives'][disk.id].append(theError)
    def checkSASdiskNoArray(self):
        errorType = list(ERRORTYPES2SEVERITY.keys())[2]
        for disk in self.dbData['harddrives']:
            if getattr(disk,'raidarray') is None:
                hnid = getattr(disk,'headnode')
                myhn = self.dbManager.session.query(PROCESSINGORDER['headnodes']).filter(PROCESSINGORDER['headnodes'].id == hnid).one()
                if myhn.raidtype == 'zfs':
                    # print("No array for this sas disk on",self.maps.hnid2hnnamemap[hnid],"but its ok because this is a ZFS server")
                    continue
                else:
                    pass
                    # print("This disk on ",self.maps.hnid2hnnamemap[hnid]," is using mdadm and should be part of a raid array.")
                if errorType not in self.detectedErrorTypes: self.detectedErrorTypes.append(errorType)
                theError = {'severity':ERRORTYPES2SEVERITY[errorType], 'description': 'This SAS disk is not part of RAID array',
                            'errorType':errorType}
                if disk.id not in self.errorsByDevTypeID['harddrives'].keys():
                    self.errorsByDevTypeID['harddrives'][disk.id] = [theError]
                else:
                    self.errorsByDevTypeID['harddrives'][disk.id].append(theError)
    def checkFailedSASpaths(self): #This will determine if any failed SAS paths exist assuming that each JBOD should have a multiple of 2 connections.
        errorType = list(ERRORTYPES2SEVERITY.keys())[7]
        hns = PROCESSINGORDER['headnodes']
        hds = PROCESSINGORDER['harddrives']
        lds = PROCESSINGORDER['logicaldisks']
        hd2ld = {}
        hn2hd = {}
        final = {}
        hrfinal = {} #human readable output version for testing
        for hd, ld in self.dbManager.session.query(hds,lds).filter(hds.id == lds.harddrive):
            if hd.id not in hd2ld:
                hd2ld[hd.id] = [ld.id]
            else:
                hd2ld[hd.id].append(ld.id)
        for hn, hd in self.dbManager.session.query(hns,hds).filter(hns.id == hds.headnode):
            if hd.id in hd2ld:
                if hn.id not in hn2hd:
                    hn2hd[hn.id] = [hd.id]
                else:
                    hn2hd[hn.id].append(hd.id)
        for hn in hn2hd:
            for hd in hn2hd[hn]:
                if len(hd2ld[hd]) < CABLESPERJBOD: # ratio of logicaldisks to harddisks should be equal to cablePerJBOD.
                    if errorType not in self.detectedErrorTypes: self.detectedErrorTypes.append(errorType)
                    theError = {'severity':ERRORTYPES2SEVERITY[errorType], 'description': 'This hard drive is missing SAS paths.',
                                'errorType':errorType}
                    if hd not in self.errorsByDevTypeID['harddrives'].keys():
                        self.errorsByDevTypeID['harddrives'][hd] = [theError]
                    else:
                        self.errorsByDevTypeID['harddrives'][hd].append(theError)
                    if hn not in final:
                        final[hn] = {hd:hd2ld[hd]}
                    else:
                        final[hn][hd] = hd2ld[hd]
        if self.debug:
            for hn in final:
                hnname = self.dbManager.session.query(hns).filter(hns.id == hn).one().name
                hrfinal[hnname] = {}
                for hd in final[hn]:
                    record = self.dbManager.session.query(hds).filter(hds.id == hd).one()
                    hdid = record.id
                    index = record.index
                    hrfinal[hnname][hdid] = [index]
                    for ld in final[hn][hd]:
                        ldname = self.dbManager.session.query(lds).filter(lds.id == ld).one().name
                        hrfinal[hnname][hdid].append(ldname)

            for host in hrfinal:
                print(host)
                print("The number of failed paths in this host is",len(hrfinal[host]))
                pprint(hrfinal[host])
    def checkFailedCables(self): #This function is dependent on having previously executed checkFailedSASpaths.
                                #It compares the number of failed SAS paths per jbod to the number of slots. if = then cable dead.
        errorType = list(ERRORTYPES2SEVERITY)[8]
        jbs = PROCESSINGORDER['jbods']
        hds = PROCESSINGORDER['harddrives']
        failedPathCounts = {}
        maphdid2jbodid = {hd.id:hd.jbod for hd in self.dbManager.session.query(hds)}
        mapjbodid2numslots = {jbd.id:jbd.numslots for jbd in self.dbManager.session.query(jbs)}
        for hdid in self.errorsByDevTypeID['harddrives']:
            for error in self.errorsByDevTypeID['harddrives'][hdid]:
                if error['errorType'] == list(ERRORTYPES2SEVERITY.keys())[7]:
                    jbodid = maphdid2jbodid[hdid]
                    if jbodid not in failedPathCounts:
                        failedPathCounts[jbodid] = 1
                    else:
                        failedPathCounts[jbodid] = failedPathCounts[jbodid] + 1
        for jbodid in failedPathCounts:
            if failedPathCounts[jbodid] == mapjbodid2numslots[jbodid]:
                if errorType not in self.detectedErrorTypes: self.detectedErrorTypes.append(errorType)
                theError = {'severity':ERRORTYPES2SEVERITY[errorType], 'errorType':errorType,
                            'description':'There is a bad cable between this JBOD and its server.'}
                if jbodid not in self.errorsByDevTypeID['jbods']:
                    self.errorsByDevTypeID['jbods'][jbodid] = [theError]
                else:
                    self.errorsByDevTypeID['jbods'][jbodid].append(theError)
        if self.debug:
            pprint(self.errorsByDevTypeID['jbods'])
    
    def createStorageErrorDBs(self):
        for tablename in self.errorsByDevTypeID:
            for iterkey in self.errorsByDevTypeID[tablename]:
                if type(iterkey) == str:
                    deviceunique = iterkey
                    devid = None

                elif type(iterkey) == int:
                    devid = iterkey
                    deviceunique = None
                else:
                    self.dbManager.session.rollback()
                    self.dbManager.session_maker.close_all()
                    raise Exception("devid is neither int not string I don't know how to handle it.\nPlease investigate createStorageErrors in dbaudit class.")
                for newerror in self.errorsByDevTypeID[tablename][iterkey]:
                    self.dbManager.session.add(storageerror(errorType=newerror['errorType'],devTable=tablename,description=newerror['description'],deviceid=devid,deviceunique=deviceunique))
        self.dbManager.session.commit()

    def buildOverviewData(self):
        overviewErrorData = {}
        allerrors = self.dbManager.session.query(storageerror)
        for errorRecord in allerrors:
            errorid = errorRecord.id
            devtype = errorRecord.devtable
            devid = errorRecord.deviceid
            errortype = errorRecord.errortype
            devunique = errorRecord.deviceunique
            severity = ERRORTYPES2SEVERITY[errortype]
            description = errorRecord.description
            moddate = str(errorRecord.modified)
            errorData = {'devtype':devtype,'devid':devid,'errortype':errortype,'devunique':devunique,'severity':severity,
                         'description':description,'modified':moddate}
            if devtype =='headnodes':#have to handle the case wher there are not records reported on a given host so it has not database id.
                if devid is None: #This can only happen with headnode records
                    identifier = devunique
                else:
                    identifier = devid
                if identifier not in overviewErrorData:
                    overviewErrorData[identifier] = {'jbods':{},'raidarrays':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='headnodes',identifier=identifier)}
                overviewErrorData[identifier]['errors'][errorid] = errorData
                overviewErrorData[identifier]['attributes']['directerror'] = True

            elif devtype == 'logicaldisks':
                hdparent = self.maps.ldid2hdidmap[devid]
                jbparent = self.maps.hdid2jbidmap[hdparent]
                raparent = self.maps.hdid2raidmap[hdparent]
                hnparent = self.maps.jbodid2hnidmap[jbparent]
                if hnparent not in overviewErrorData:
                    overviewErrorData[hnparent] = {'jbods':{},'raidarrays':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='headnodes',identifier=hnparent)}
                if jbparent not in overviewErrorData[hnparent]['jbods']:
                    overviewErrorData[hnparent]['jbods'][jbparent] = {'disks':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='jbods',identifier=jbparent)}
                if hdparent not in overviewErrorData[hnparent]['jbods'][jbparent]['disks']:
                    overviewErrorData[hnparent]['jbods'][jbparent]['disks'][hdparent] = {'errors':{},'logicaldisks':{},'attributes':self.getDefaultAttrs(tablename='harddrives',identifier=hdparent)}
                if devid not in overviewErrorData[hnparent]['jbods'][jbparent]['disks'][hdparent]['logicaldisks']:
                    overviewErrorData[hnparent][jbparent]['jbods']['disks'][hdparent]['logicaldisks'][devid] = {'errors':{},'attributes':self.getDefaultAttrs(tablename='logicaldisks',identifier=devid)}
                #Set nestederror flags for each level and directerror flags for bottom level. This is used by GUI for highlighting errored trees.
                overviewErrorData[hnparent]['attributes']['nestederror'] = True
                overviewErrorData[hnparent]['jbods'][jbparent]['attributes']['nestederror'] = True
                overviewErrorData[hnparent]['jbods'][jbparent]['disks'][hdparent]['attributes']['nestederror'] = True
                overviewErrorData[hnparent]['jbods'][jbparent]['disks'][hdparent]['logicaldisks'][devid]['attributes']['directerror'] = True
                overviewErrorData[hnparent]['jbods'][jbparent]['disks'][hdparent]['logicaldisks'][devid]['errors'][errorid] = errorData

            elif devtype == 'harddrives':
                jbparent = self.maps.hdid2jbidmap[devid]
                raparent = self.maps.hdid2raidmap[devid]
                hnparent = self.maps.jbodid2hnidmap[jbparent]
                # if not byhnid:
                #     hnparent = self.maps.hnid2hnnamemap[hnparent]
                if hnparent not in overviewErrorData:
                    overviewErrorData[hnparent] = {'jbods':{},'raidarrays':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='headnodes',identifier=hnparent)}
                if jbparent not in overviewErrorData[hnparent]['jbods']:
                    overviewErrorData[hnparent]['jbods'][jbparent] = {'disks':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='jbods',identifier=jbparent)}
                if raparent is not None and raparent not in overviewErrorData[hnparent]['raidarrays']:
                    overviewErrorData[hnparent]['raidarrays'][raparent] = {'disks':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='raidarrays',identifier=raparent)}
                if devid not in overviewErrorData[hnparent]['jbods'][jbparent]['disks']:
                    overviewErrorData[hnparent]['jbods'][jbparent]['disks'][devid] = {'logicaldisks':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='harddrives',identifier=devid)}
                if raparent is not None and devid not in overviewErrorData[hnparent]['raidarrays'][raparent]['disks']:
                    overviewErrorData[hnparent]['raidarrays'][raparent]['disks'][devid] = {'errors':{},'disks':{},'attributes':self.getDefaultAttrs(tablename='raidarrays',identifier=raparent)}
                overviewErrorData[hnparent]['attributes']['nestederror'] = True
                overviewErrorData[hnparent]['jbods'][jbparent]['attributes']['nestederror'] = True
                if raparent is not None:
                    overviewErrorData[hnparent]['raidarrays'][raparent]['attributes']['nestederror'] = True
                overviewErrorData[hnparent]['jbods'][jbparent]['disks'][devid]['attributes']['directerror'] = True
                overviewErrorData[hnparent]['jbods'][jbparent]['disks'][devid]['errors'][errorid] = errorData
                if raparent is not None:
                    overviewErrorData[hnparent]['raidarrays'][raparent]['disks'][devid]['errors'][errorid] = errorData


            elif devtype == 'raidarrays':
                hnparent = self.maps.raid2hnidmap[devid]
                if hnparent not in overviewErrorData:
                    overviewErrorData[hnparent] = {'jbods':{},'raidarrays':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='headnodes',identifier=hnparent)}
                if devid not in overviewErrorData[hnparent]['raidarrays']:
                    overviewErrorData[hnparent]['raidarrays'][devid] = {'disks':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='raidarrays',identifier=devid)}
                overviewErrorData[hnparent]['attributes']['nestederror'] = True
                overviewErrorData[hnparent]['raidarrays'][devid]['attributes']['directerror'] = True
                overviewErrorData[hnparent]['raidarrays'][devid]['errors'][errorid] = errorData

            elif devtype == 'jbods':
                hnparent = self.maps.jbodid2hnidmap[devid]
                if hnparent not in overviewErrorData:
                    overviewErrorData[hnparent] = {'jbods':{},'raidarrays':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='headnodes',identifier=hnparent)}
                if devid not in overviewErrorData[hnparent]['jbods']:
                        overviewErrorData[hnparent]['jbods'][devid] = {'disks':{},'errors':{},'attributes':self.getDefaultAttrs(tablename='jbods',identifier=devid)}
                overviewErrorData[hnparent]['attributes']['nestederror'] = True
                overviewErrorData[hnparent]['jbods'][devid]['attributes']['directerror'] = True
                overviewErrorData[hnparent]['jbods'][devid]['errors'][errorid] = errorData
        self.overviewErrorData = overviewErrorData
        return overviewErrorData
    def countTotalErrors(self):
        smartstatuserrors = []
        errorsCountByType = {errorType:0 for errorType in list(ERRORTYPES2SEVERITY.keys())}
        totalErrorCount = 0
        for server in self.overviewErrorData:
            totalErrorCount = totalErrorCount + len(self.overviewErrorData[server]['errors'])
            for error in self.overviewErrorData[server]['errors']:
                etype = self.overviewErrorData[server]['errors'][error]['errortype']
                errorsCountByType[etype] = errorsCountByType[etype] +1
            for ra in self.overviewErrorData[server]['raidarrays']:
                totalErrorCount = totalErrorCount + len(self.overviewErrorData[server]['raidarrays'][ra]['errors'])
                for error in self.overviewErrorData[server]['raidarrays'][ra]['errors']:
                    etype = self.overviewErrorData[server]['raidarrays'][ra]['errors'][error]['errortype']
                    errorsCountByType[etype] = errorsCountByType[etype] +1
            for chassis in self.overviewErrorData[server]['jbods']:
                totalErrorCount = totalErrorCount + len(self.overviewErrorData[server]['jbods'][chassis]['errors'])
                for error in self.overviewErrorData[server]['jbods'][chassis]['errors']:
                    etype = self.overviewErrorData[server]['jbods'][chassis]['errors'][error]['errortype']
                    errorsCountByType[etype] = errorsCountByType[etype] +1
                for disk in self.overviewErrorData[server]['jbods'][chassis]['disks']:
                    totalErrorCount = totalErrorCount + len(self.overviewErrorData[server]['jbods'][chassis]['disks'][disk]['errors'])
                    for error in self.overviewErrorData[server]['jbods'][chassis]['disks'][disk]['errors']:
                        etype = self.overviewErrorData[server]['jbods'][chassis]['disks'][disk]['errors'][error]['errortype']
                        if etype == "smartstatus":
                            smartstatuserrors.append(error)
                        errorsCountByType[etype] = errorsCountByType[etype] +1
                    for logdisk in self.overviewErrorData[server]['jbods'][chassis]['disks'][disk]['logicaldisks']:
                        totalErrorCount = totalErrorCount + len(self.overviewErrorData[server]['jbods'][chassis]['disks'][disk]['logicaldisks'][logdisk]['errors'])
                        for error in self.overviewErrorData[server]['jbods'][chassis]['disks'][disk]['logicaldisks'][logdisk]['errors']:
                            etype = self.overviewErrorData[server]['jbods'][chassis]['disks'][disk]['logicaldisks'][logdisk]['errors'][error]['errortype']
                            errorsCountByType[etype] = errorsCountByType[etype] +1
        for item in smartstatuserrors:
            print(item,"\n")
        smartstatuserrors.sort()
        for item in smartstatuserrors:
            print(item,"\n")
        return {'errorsCountByType':errorsCountByType,'totalErrorCount':totalErrorCount}
    def __repr__(self):
        pprint(self.errorsByDevTypeID, width=300)

    def getDefaultAttrs(self,tablename,identifier):
        attrs = {'direct':False,'nested':False,'id':identifier,'displayname':identifier}
        tablename2map = {'jbods':self.maps.jbid2displayname,'raidarrays':self.maps.raid2displayname,'harddrives':self.maps.hdid2displayname,
                         'logicaldisks':self.maps.ldid2displayname}
        if tablename == 'headnodes':
            if type(identifier) == int:
                attrs['displayname'] = self.maps.hnid2displayname[identifier]
            elif type(identifier) == str:
                attrs['id'] = None
            return attrs
        if tablename in tablename2map:
            return {'direct':False,'nested':False,'id':identifier,'displayname':tablename2map[tablename][identifier]}
        else:
            raise Exception("In class dbaudit I tried to getDefaultAttrs for a tablename that doesn't exist.")



class idmapper(object):
    def __init__(self,dbData = None):
        if dbData is None:
            dbMan = db_manager()
            dbData = {tableType:dbMan.session.query(PROCESSINGORDER[tableType]) for tableType in PROCESSINGORDER}
        self.hnid2hnnamemap = dict({hn.id:hn.name for hn in dbData['headnodes']})
        self.jbodid2hnidmap = dict({jb.id:jb.headnode for jb in dbData['jbods']})
        self.raid2hnidmap =  dict({ra.id:ra.headnode for ra in dbData['raidarrays']})
        self.hdid2jbidmap = dict({hd.id:hd.jbod for hd in dbData['harddrives']})
        self.hdid2raidmap = dict({hd.id:hd.raidarray for hd in dbData['harddrives']})
        self.hdid2hnidmap = dict({hd.id:hd.headnode for hd in dbData['harddrives']})
        self.ldid2hdidmap = dict({ld.id:ld.harddrive for ld in dbData['logicaldisks']})
        self.hnid2displayname = dict({hn.id:hn.name for hn in dbData['headnodes']})
        self.jbid2displayname = dict({jb.id:jb.logicalid for jb in dbData['jbods']})
        self.raid2displayname = dict({ra.id:ra.name for ra in dbData['raidarrays']})
        self.hdid2displayname = dict({hd.id:hd.serialnumber for hd in dbData['harddrives']})
        self.ldid2displayname = dict({ld.id:ld.name for ld in dbData['logicaldisks']})
    def __repr__(self):
        maps = {'hnid2displayname':self.hnid2displayname,'jbid2displayname':self.jbid2displayname,'raid2displayname':self.raid2displayname,
         'hdid2displayname':self.hdid2displayname,'ldid2displayname':self.ldid2displayname}
        return json.dumps(maps)
    def getDisplayNameMaps(self):
        return {'headnodes':self.hnid2displayname,'jbods':self.jbid2displayname,'raidarrays':self.raid2displayname,
         'harddrives':self.hdid2displayname,'logicaldrives':self.ldid2displayname}

