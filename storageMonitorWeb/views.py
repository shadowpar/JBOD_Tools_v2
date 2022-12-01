from . import app
from flask import render_template, request, url_for, redirect
from .webdata import storage_system_failures, statGatherer
from .webdata import displayJBOD
from pprint import pprint, pformat
from .webdata import statusTree
from sys import getsizeof
from pathlib import Path
from hancockStorageMonitor.database.db_manager import db_manager
from hancockStorageMonitor.database.sqlalchemy_classes import storageerror
from hancockStorageMonitor.common.staticdatacentral import PROCESSINGORDER, DBSEARCHKEYS
from hancockStorageMonitor.common.staticdatastorage import SEVERITYLEVELS, ERRORTYPES2SEVERITY
from hancockStorageMonitor.common.staticdatacentral import ERRORTYPES2DEVTYPE
import json
from sqlalchemy.orm.exc import NoResultFound
from collections import OrderedDict

dbman = db_manager()
tempLogPath = Path('/var/log/storageMonitor').joinpath('testing.log')
staticErrorDataFile = Path(__file__).parent.absolute().parent.absolute().joinpath('flatdata').joinpath('errorData.json')
# Just a little security check on post parameter values.
acceptablePostKeys = ['severityall','severitychoose','deviceall','devicechoose','errorall','errorchoose']
acceptablePostKeys.extend(PROCESSINGORDER.keys())
acceptablePostKeys.extend(list(ERRORTYPES2SEVERITY.keys()))
acceptablePostValues = {key:[True,False] for key in acceptablePostKeys}

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/failures",methods=['GET','POST'])
def failures():
    with staticErrorDataFile.open() as f:
         failureData = json.load(f)
    failureData = {key:failureData[key] for key in failureData if len(failureData[key]) > 0}
    if len(failureData) == 0:
        return render_template('nofailures.html')
        #Set default view data on get request or refresh for radio buttons
    viewdata = {'severityall':True,'severitychoose':False,'devicechoose':False,'deviceall':True,'errorchoose':False,'errorall':True}
    severityPresent = list(dict.fromkeys([ERRORTYPES2SEVERITY[key] for key in failureData]))
    devTypesPresent = list(dict.fromkeys([ERRORTYPES2DEVTYPE[key] for key in failureData]))
    # Programmatically add default settings for check boxes.
    for key in devTypesPresent:#dynamically add devTypes present in failure data.
        viewdata[key] = True
    for key in severityPresent:# Getting severity levels present in failuredata
        viewdata[key+str('severity')] = True
    for key in failureData:# dynamically add settings for errorTypes present in error data.
        viewdata[key] = True
    if request.method == 'post':
        for key in request.args:
            if key in viewdata:
                argdata = request.args[key]
                if argdata in acceptablePostValues[key]:
                    viewdata[key] = request.args[key]
    tempLogPath = Path('/var/log/storageMonitor').joinpath('testing.log')
    # with tempLogPath.open(mode='w') as f:
    #     f.write("Contents of severityPresent\n")
    #     f.write(pformat(severityPresent))
    #     f.write("\nContents of devTypesPresent\n")
    #     f.write(pformat(devTypesPresent))
    #     f.write("\nContents of failureData\n")
        # f.write(pformat(failureData))
    tableColumns = list(failureData.keys())
    return render_template('failures.html',viewdata=json.dumps(viewdata), failureData=failureData, fdata=json.dumps(failureData), severityPresent=severityPresent, devTypesPresent=devTypesPresent)
    # return render_template('nofailures.html')


@app.route("/statistics",methods=['GET'])
def statistics():
    stats = statGatherer()
    pprint(stats.serverStats)
    return render_template('statistics.html',stats=stats)

@app.route("/jbodview",methods=['GET','POST'])
def jbodview():
    try:
        print("entered jbodview view page try statement")
        if request.method == "POST":
            print("Entering post if statement branch")
            targetJBOD = request.form['targetJBOD']
        else:
            targetJBOD = 'USWSJ05018EA002E'
    except Exception as e:
        targetJBOD = None
        print(e)
    if targetJBOD is not None:
        theJBOD = displayJBOD(targetJBOD)
    return render_template('JBODview.html',attributes=theJBOD.attributes,disks=theJBOD.disks)

@app.route("/overview",methods=['GET','POST'])
def overview():
    overview = statusTree(serverlist='all')
    data = overview.status_tree
    tempLogPath = Path('/var/log/storageMonitor').joinpath('testing.log')
    # with tempLogPath.open(mode='w') as f:
    #     f.write(pformat(data))
    treedata = {'qgp006.rcf.bnl.gov':{'jbods':{},'raidarrays':{},'attributes':{'name':'myname'}}}
    print("The tree data is this many bytes",getsizeof(treedata))
    # pprint(overview.status_tree)
    return render_template('overview.html', treedata=json.dumps(data))

@app.after_request
def add_header(response):
    response.cache_control.max_age = 30
    return response

@app.route("/failoverview",methods=['GET','POST'])
def failoveroverview():
    data = json.loads(staticErrorDataFile.read_text())
    displaymaps = data['displayNameMaps']
    data = data['overviewErrorData']
    if len(data) == 0:
        return render_template('nofailures.html')
    if request.method == 'POST':
        viewdata = json.loads(request.values['viewdata'])
        detailfocus = json.loads(request.values['detailfocus'])

        devdetails = getDevData(identifier=detailfocus['devid'],tabletype=detailfocus['devtype'])
    else:
       viewdata = {'ActiveIDs':[],'OpenIDs':[]}
       devdetails = getDevData(list(data.keys())[0], 'headnodes')
    # for device in devdetails:
    #     devdetails[device].update(data[])
    return render_template('failoverview.html', treedata=json.dumps(data), viewdata=json.dumps(viewdata),detailfocus = json.dumps(devdetails), displaymaps=json.dumps(displaymaps))

def getDevData(identifier, tabletype):
    try:
        identifier = int(identifier)
    except ValueError:
        pass
    with tempLogPath.open('w') as f:
        f.write("\nContents of arguments passed to getDevData\n")
        f.write(str(identifier))
        f.write(tabletype)
    if type(identifier) == str:
        lookup = DBSEARCHKEYS[PROCESSINGORDER[tabletype]]
        errorlookup = 'deviceunique'
        with tempLogPath.open('a') as f:
            f.write("\nContents of its a string\n")
            f.write(errorlookup)
            f.write(lookup)
    elif type(identifier) == int:
        lookup = 'id'
        errorlookup = 'deviceid'
        with tempLogPath.open('a') as f:
            f.write("\nContents of its an int\n")
            f.write(str(lookup))
            f.write(' '+str(errorlookup))
    else:
        return None
    data = {'identifier':identifier}
    try:
        datafromdb = dbman.session.query(PROCESSINGORDER[tabletype]).filter(getattr(PROCESSINGORDER[tabletype], lookup) == identifier).one()
        data['attributes'] = datafromdb.returnImportantProperties()
    except NoResultFound:
        data['attributes'] = {}

    with tempLogPath.open('a') as f:
        f.write("\ncontents of data in getDevData\n")
        f.write(pformat(data))
    try:
        errdata = dbman.session.query(storageerror).filter(getattr(storageerror,errorlookup) == identifier)
        data['errors'] = [err.returnImportantProperties() for err in errdata]
    except NoResultFound:
        data['errors'] = []
    with tempLogPath.open('a') as f:
        f.write("\ncontents of data in getDevData revised\n")
        f.write(pformat(data))

    return data