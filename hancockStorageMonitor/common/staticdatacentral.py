from hancockStorageMonitor.database.sqlalchemy_classes import cpu, headnode,harddrive,logicaldisk, jbod, raidarray
from collections import OrderedDict

DBSEARCHKEYS = {cpu: 'model', headnode: 'name', jbod: 'serialnumber', harddrive: 'serialnumber', logicaldisk:('serialnumber', 'name'), raidarray: 'uuid'}
PROCESSINGORDER = OrderedDict({getattr(className, '__tablename__'):className for className in [cpu, headnode, raidarray, jbod, harddrive, logicaldisk]})
DBREFERENCES = {'logicaldisks':['harddrives'], 'harddrives':['headnodes', 'raidarrays', 'jbods'], 'jbods':['headnodes'], 'raidarrays':['headnodes'], 'headnodes':['cpus'], 'cpus':[]}
DBDISPLAYNAMES = {'logicaldisks': 'name', 'harddrives': 'serialnumber', 'jbods': 'serialnumber', 'raidarrays': 'name', 'headnodes': 'name', 'cpus': 'model'}
PK = list(PROCESSINGORDER.keys()) # a list of db table names whichi identify a certain kind of device record.
ERRORTYPES2DEVTYPE = {'olddata':PK[1], 'smartstatus':PK[4], 'sasdisknoarray':PK[4], 'uncorrectederrors':PK[4], 'growndefects':PK[4],
                        'missingrecords':PK[1], 'raidarraystate':PK[2], 'failedpaths':PK[4], 'failedcables':PK[3]}

