from hancockStorageMonitor.database.sqlalchemy_classes import headnode, jbod, harddrive, logicaldisk, cpu, raidarray
from hancockStorageMonitor.common.staticdatacentral import DBSEARCHKEYS, PROCESSINGORDER
from hancockStorageMonitor.database.dbOps import mass_db_insert, translateAndCreate, clearDB
from datetime import datetime
import json
from hancockStorageMonitor.database.db_manager import db_manager
from shutil import rmtree
from os import remove as deleteFile
from hancockStorageMonitor.common.staticdatastorage import EXPERIMENTS, allhosts
from pathlib import Path
from hancockStorageMonitor.common.ssh import ssh_get_remote_file
from hancockStorageMonitor.localgatherers.scsiOperations import multiExecute

def getHostDats(experiments=[],remoteFileLocalPath=Path('/tmp/storageMonitor')):
    datFiles = {}
    for experiment in experiments:
        datFiles[experiment] =  remoteFileLocalPath.joinpath(experiment).glob("*_storageMonitor.dat")
    output = {}
    for experiment in datFiles:
        output[experiment] = {}
        for filePath in datFiles[experiment]:
            output[experiment][filePath.name] = json.load(filePath.open(mode='r'))
    return output

def getRemoteDataFiles(experiment,host,remoteFileLocalPath='/tmp/storageMonitor'):
        remoteFilename = Path('/tmp').joinpath(host + '_storageMonitor.dat').as_posix()
        localFilename = Path(remoteFileLocalPath).joinpath(experiment).joinpath(host + '_storageMonitor.dat').as_posix()
        returnCode = ssh_get_remote_file(remoteHost=host, remoteFileName=remoteFilename,
                                         localFileName=localFilename)
        if returnCode != 0:
            errors = ['', 'The host could not be reached.\n', 'The data file was not found.\n']
            errorString = str(
                datetime.now()) + " There was an error trying to retrieve data from " + host + "\n" + str(errors[returnCode])
            with errorLog.open(mode='a') as log:  # Log any errors reaching hosts
                log.write(errorString)
            if returnCode == 2:
                deleteFile(localFilename)
        return returnCode

logPath = Path('/var').joinpath('log').joinpath('storageMonitor')
if not  logPath.is_dir(): logPath.mkdir(mode=777)
mainLog = logPath.joinpath('storageMonitor.log')
errorLog = logPath.joinpath('errors.log')

#Maintain consistency with changing cron choices. Additionally, cron is setup by manually running the associated program once.
associatedCron = Path('/etc').joinpath('cron.d').joinpath('storageMonitorCentral.cron')
localCronCopy = Path('hancockStorageMonitor').joinpath('common').joinpath('storageMonitorCentral.cron')
# if not associatedCron.is_file() or associatedCron.read_text() != localCronCopy.read_text():
#     associatedCron.write_text(localCronCopy.read_text())



# Here the non function cade beings. We should separate this into a different program file.
remoteFileLocalPath = Path('/tmp').joinpath('storageMonitor')

# Housecleaning. Removing any empty strings brought in from host list files.
allhosts = {experiment:[host for host in allhosts[experiment] if host != ''] for experiment in allhosts}
# Flush old data files before beginning run.
if remoteFileLocalPath.is_dir():
    rmtree(remoteFileLocalPath)
remoteFileLocalPath.mkdir()

# Clear the error log file from the last run.
errorLog.write_text("Error log for storageMonitor data run executed on "+str(datetime.now())+"\n")

multiargs = []
for experiment in allhosts:
    if not remoteFileLocalPath.joinpath(experiment).is_dir():
        remoteFileLocalPath.joinpath(experiment).mkdir()
    for host in allhosts[experiment]:
        args = {'experiment':experiment,'host':host,'remoteFileLocalPath':remoteFileLocalPath.as_posix()}
        multiargs.append(args)
results = multiExecute(functionName=getRemoteDataFiles,kwargs=multiargs)


# Create a dictionary of host data imported from from files copied from each storage host. This is sorted by experiment.
newData = getHostDats(experiments=EXPERIMENTS, remoteFileLocalPath=remoteFileLocalPath)
# We process the data to create a list of each type of new database objects across all hosts. i.e. cpus, headnodes, harddrives etc.
# We also insert in a few properties such as modified timestamp and experiment.
# Later we will use this section to mix in other static data such as physical locations.
tableNamedData = {tablename:[] for tablename in PROCESSINGORDER}
newDbObjects = {tablename:[] for tablename in PROCESSINGORDER}
for experiment in newData:
    for datFile in newData[experiment]:
        modified = datetime.fromtimestamp(newData[experiment][datFile]['modified'])
        for tablename in PROCESSINGORDER:
            for newObjID in newData[experiment][datFile][tablename]:
                newObjData = newData[experiment][datFile][tablename][newObjID]
                newObjData.update({'modified':modified,'experiment':experiment})
                tableNamedData[tablename].append(newObjData)
#deduplicate CPU list since the same CPU may exist in many servers.
existingCPUSs = []
dedupCPUs = []

for processor in tableNamedData['cpus']:
    if processor[DBSEARCHKEYS[cpu]] not in existingCPUSs:
        existingCPUSs.append(processor[DBSEARCHKEYS[cpu]])
        dedupCPUs.append(processor)
tableNamedData['cpus'] = dedupCPUs
#create database connection
myDbManager = db_manager()
myDbManager.session.query()
#Clear the current database contents to ensure no stale data.
clearDB(myDbManager.session)
# Create CPU database objects for each unique CPU
newDbObjects['cpus'] = [translateAndCreate(currObj=cpuObj,transType=cpu) for cpuObj in tableNamedData['cpus']]
newDbObjects['cpus'] = [item for item in newDbObjects['cpus'] if item is not None]

mass_db_insert(myDbManager.session,newDbObjs=newDbObjects['cpus'])
# Create headnode objects for each server

#First we need to create a map of cpu id to cpu model so that we can lookup the headnode(cpu=) value
cpuObjs = myDbManager.session.query(cpu)
cpuidmap = {getattr(cpuObj,'model'):getattr(cpuObj,'id') for cpuObj in cpuObjs}

#Now we can create headnode objects using the appropriate cpu id value from cpuidmap referenced against headnode's cpumodel property.
newDbObjects['headnodes'] = [translateAndCreate(currObj=headnodeObj,transType=headnode,auxData={cpu:cpuidmap}) for headnodeObj in tableNamedData['headnodes']]
newDbObjects['headnodes'] = [item for item in newDbObjects['headnodes'] if item is not None]
mass_db_insert(sessionObj=myDbManager.session,newDbObjs=newDbObjects['headnodes'])

# Next up we create jbod objects to put into the database. First we get a fresh copy of the server model to headnode id mapping.
headnodeObjs = myDbManager.session.query(headnode)
headnodeidmap = {getattr(headnodeObj,'name'):getattr(headnodeObj,'id') for headnodeObj in headnodeObjs}
newDbObjects['jbods'] = [translateAndCreate(currObj=jbodObj,transType=jbod,auxData={headnode:headnodeidmap}) for jbodObj in tableNamedData['jbods']]
newDbObjects['jbods'] = [item for item in newDbObjects['jbods'] if item is not None]
mass_db_insert(sessionObj=myDbManager.session,newDbObjs=newDbObjects['jbods'])


#Now we create raid array objects. These have references to headnode objects so we get a fresh copy of headnode name to id mapping and pass it as aux data
headnodeidmap = {getattr(headnodeObj,'name'):getattr(headnodeObj,'id') for headnodeObj in headnodeObjs}
newDbObjects['raidarrays'] = [translateAndCreate(currObj=raObj,transType=raidarray,auxData={headnode:headnodeidmap}) for raObj in tableNamedData['raidarrays']]
newDbObjects['raidarrays'] = [item for item in newDbObjects['raidarrays'] if item is not None]
mass_db_insert(sessionObj=myDbManager.session,newDbObjs=newDbObjects['raidarrays'])

# Now we create harddrives objects. harddrive reference raid array, headnode, and jbod so all three auxData must be passed in
headnodeObjs = myDbManager.session.query(headnode)
headnodeidmap = {getattr(headnodeObj,'name'):getattr(headnodeObj,'id') for headnodeObj in headnodeObjs}
jbodObjs = myDbManager.session.query(jbod)
jbodidmap = {getattr(jbodObj,'serialnumber'):getattr(jbodObj,'id') for jbodObj in jbodObjs}
raObjs = myDbManager.session.query(raidarray)
raidmap = {getattr(raObj,'uuid'):getattr(raObj,'id') for raObj in raObjs}
auxData = {headnode:headnodeidmap,jbod:jbodidmap,raidarray:raidmap}
newDbObjects['harddrives'] = [translateAndCreate(currObj=hdObj,transType=harddrive,auxData=auxData) for hdObj in tableNamedData['harddrives']]
newDbObjects['harddrives'] = [item for item in newDbObjects['harddrives'] if item is not None]
mass_db_insert(sessionObj=myDbManager.session,newDbObjs=newDbObjects['harddrives'])

#Now we create logical disks objects. Logical Disk objects reference harddrives. So get auxData for harddrives
hdObjs = myDbManager.session.query(harddrive)
hdidmap = {getattr(hdObj,'serialnumber'):getattr(hdObj,'id') for hdObj in hdObjs}
newDbObjects['logicaldisks'] = [translateAndCreate(currObj=ldObj,transType=logicaldisk,auxData={harddrive:hdidmap}) for ldObj in tableNamedData['logicaldisks']]
newDbObjects['logicaldisks'] = [item for item in newDbObjects['logicaldisks'] if item is not None]
mass_db_insert(sessionObj=myDbManager.session,newDbObjs=newDbObjects['logicaldisks'])
#Done with database operations. CLosing all sessions.
myDbManager.session_maker.close_all()