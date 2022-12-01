from hancockStorageMonitor.database.sqlalchemy_classes import headnode, cpu
from hancockStorageMonitor.database.db_manager import db_manager

class statGatherer(object):
    def __init__(self,qtype='all',headnodename=None,jbodserial=None,hdserial=None,experiment=None,raidarrayname=None):
        self.db_manager = db_manager()
        self.statistics = {'server':{},'jbod':{},'harddrive':{}}
        self.headnodename = headnodename
        self.jbodserial = jbodserial
        self.hdserial = hdserial
        self.experimentname = experiment
        self.raidarrayname = raidarrayname
        self.serverStats = {}
        self.serverCount = None
        self.qtypes = {'all':self.gatherAll(),
                                'headnode':self.gatherServerStatistics(headnodename=self.headnodename),
                                'jbod':self.gatherJBODStatistcs(jbodserial=self.jbodserial),
                                'harddrive':self.gatherHardDriveStatistics(hdserial=self.hdserial),
                                'raidarray':self.gatherRaidArrayStatistics(raidarrayname=self.raidarrayname),
                                'experiment':self.gatherExperimentStatistics(experimentname=self.experimentname)}
        # self.qtypes[qtype]


    def gatherAll(self):
        cpus = self.db_manager.session.query(cpu)
        cpuid2model = {item.id:item.model for item in cpus}
        servers = self.db_manager.session.query(headnode)
        self.serverStats['number'] = servers.count()
        self.serverStats['numberbyexperiment'] = {}
        self.serverStats['numberbydatacenter'] = {}
        self.serverStats['numberbyservermodel'] = {}
        self.serverStats['numberbycpumodel'] = {}
        for item in servers:
            experiment = item.experiment
            datacenter = item.datacenter
            servermodel = item.model
            if item.cpu is not -1:
                cpumodel = cpuid2model[item.cpu]
            else:
                cpumodel = ''
                
            if cpumodel in self.serverStats['numberbycpumodel']:
                self.serverStats['numberbycpumodel'][cpumodel] = int(self.serverStats['numberbycpumodel'][cpumodel]) +1
            else:
                self.serverStats['numberbycpumodel'][cpumodel] = 1
            
            if servermodel in self.serverStats['numberbyservermodel']:
                self.serverStats['numberbyservermodel'][servermodel] = int(self.serverStats['numberbyservermodel'][servermodel]) +1
            else:
                self.serverStats['numberbyservermodel'][servermodel] = 1
            
            
            if datacenter in self.serverStats['numberbydatacenter']:
                self.serverStats['numberbydatacenter'][datacenter] = int(self.serverStats['numberbydatacenter'][datacenter]) +1
            else:
                self.serverStats['numberbydatacenter'][datacenter] = 1
            
            if experiment in self.serverStats['numberbyexperiment']:
                self.serverStats['numberbyexperiment'][experiment] = int(self.serverStats['numberbyexperiment'][experiment]) +1
            else:
                self.serverStats['numberbyexperiment'][experiment] = 1

    def gatherServerStatistics(self,headnodename):
        if headnodename is None:
            return None
        serverCount = self.db_manager.session.query(headnode.id).filter()
        serverCount = int(serverCount)/1024/1024/1024/1024
        print(type(serverCount))
        print(serverCount)
        self.serverCount = serverCount

    def gatherJBODStatistcs(self,jbodserial):
        if jbodserial is None:
            return None

    def gatherHardDriveStatistics(self,hdserial):
        if hdserial is None:
            return None
        pass

    def gatherExperimentStatistics(self,experimentname):
        if experimentname is None:
            return None
    def gatherRaidArrayStatistics(self,raidarrayname):
        if raidarrayname is None:
            return None

