from hancockStorageMonitor.database.sqlalchemy_classes import headnode, raidarray
from hancockStorageMonitor.database.db_manager import db_manager

class sw_raid_failures(object):
    def __init__(self):
            self.db_manager = db_manager()
            self.failed_hosts = {}  #dictionary of the form {$serverName:{'id':idnumber,'failedArrays':{badArray}}}
            for selector in ['diskCompare','active','mountpoint','bitmapfile']:
                self.checkIssues(selector=selector)


    def checkIssues(self,selector):  # This function takes an argument that specifics the issue type to use in the  lookups fro query and failedProperties dictionaries.
        queries = {'diskCompare':self.db_manager.session.query(raidarray).filter(raidarray.activenumdisks != raidarray.totalnumdisks),
                   'active':self.db_manager.session.query(raidarray).filter(raidarray.active != True),
                   'mountpoint':self.db_manager.session.query(raidarray).filter(raidarray.mountpoint == '' or raidarray.mountpoint == 'error'),
                   'bitmapfile':self.db_manager.session.query(raidarray).filter(raidarray.bitmapfile == 'error')}

        failedProperties = {'diskCompare':['activenumdisks','totalnumdisks'],'active':['active'], 'mountpoint':['mountpoint'],'bitmapfile':['bitmapfile']}

        badArrays = queries[selector]
        for badArray in badArrays:
            server = self.db_manager.session.query(headnode).filter(headnode.id == badArray.headnode).first()
            if server.name not in self.failed_hosts:
                self.failed_hosts[server.name] = {'id':server.id,'failedArrays':{badArray.name:badArray.returnImportantProperties()},'failed_tests':{badArray.name:failedProperties[selector]}}
            elif server.name in self.failed_hosts:
                if badArray.name not in self.failed_hosts[server.name]['failedArrays']:
                    self.failed_hosts[server.name]['failedArrays'][badArray.name] = badArray.returnImportantProperties()
                if badArray.name not in self.failed_hosts[server.name]['failed_tests']:
                    self.failed_hosts[server.name]['failed_tests'][badArray.name] = failedProperties[selector]
                elif badArray.name in self.failed_hosts[server.name]['failed_tests']:
                    self.failed_hosts[server.name]['failed_tests'][badArray.name] = self.failed_hosts[server.name]['failed_tests'][badArray.name]+failedProperties[selector]

class server_failures(object):
    def __init__(self):
        self.db_manager = db_manager()
        self.failed_hosts = {}  #dictionary of the form {$serverName:{'id':idnumber,'failedArrays':{badArray}}}
        for selector in ['diskCompare','active','mountpoint']:
            self.checkIssues(selector=selector)
    def checkIssues(self,selector):
        pass

class jbod_failures(object):
    def __init__(self):
        self.db_manager = db_manager()
        self.failed_hosts = {}  #dictionary of the form {$serverName:{'id':idnumber,'failedArrays':{badArray}}}
        for selector in ['diskCompare','active','mountpoint']:
            self.checkIssues(selector=selector)
    def checkIssues(self,selector):
        pass

class hw_raid_failures(object):
    def __init__(self,):
        self.db_manager = db_manager()
        self.failed_hosts = {}  #dictionary of the form {$serverName:{'id':idnumber,'failedArrays':{badArray}}}
        for selector in ['diskCompare','active','mountpoint']:
            self.checkServerIssues(selector=selector)
    def checkServerIssues(self,selector):
        pass

class storage_system_failures(object):
    def __init__(self):
        self.failed_hosts = {}
        self.sw_raid_failures = sw_raid_failures()
        self.server_failures = server_failures()
        self.jbod_failures = jbod_failures()
        self.hw_raid_failures = hw_raid_failures()
        self.combineFailures()

    def combineFailures(self):
        for server in self.sw_raid_failures.failed_hosts:
            if server not in self.failed_hosts:
                self.failed_hosts[server] = self.sw_raid_failures.failed_hosts[server]
            else:
                for item in self.sw_raid_failures.failed_hosts[server]:
                    if item not in self.failed_hosts[server]:
                        self.failed_hosts[server][item] = self.sw_raid_failures.failed_hosts[server][item]

