from hancockStorageMonitor.database.db_manager import db_manager
from hancockStorageMonitor.database.sqlalchemy_classes import headnode, raidarray, jbod, harddrive, logicaldisk
from pprint import pprint

class statusTree(object):
    def __init__(self, serverlist='all'):
        print("entering status tree.")
        self.dbmanager = db_manager()
        self.serverlist = serverlist
        self.session = self.dbmanager.session
        self.status_tree = {}
        self.headnodeidmap = {}
        self.jbodidmap = {}
        self.harddrivesidmap = {}
        self.raidarraysidmap = {}
        self.hdinra = {}
        if serverlist == 'all':
            self.getAllServers()
        elif type(serverlist) == list:
            self.getServersInList()
        else:
            raise Exception("You must pass in a list of servers or leave the serverList parameter blank.")
        self.getRAIDarrays()
        self.getJBODS()
        self.getharddrives()
        self.getLogicalDisks()
        self.dbmanager.session_maker.close_all()
        print("exiting status tree")
        #self.debug_print()



    def getAllServers(self):
        servers = self.session.query(headnode).order_by(headnode.name)
        if servers is not None:
            for server in servers:
                self.headnodeidmap[server.id] = server.name
                self.status_tree[server.name] = {'attributes':server.returnImportantProperties(),'jbods':{},'raidarrays':{}}
        # self.session.expunge_all()

    def getServersInList(self):
        for target in self.serverlist:
            servers = self.session.query(headnode).filter(headnode.name == target).order_by(headnode.name)
            if servers is not None:
                for server in servers:
                    self.status_tree[server.name] = {'attributes': server.returnImportantProperties(), 'jbods': {},'raidarrays': {}}
                    self.headnodeidmap[server.id] = server.name
        # self.session.expunge_all()

    def getRAIDarrays(self):
        raidarrays = self.session.query(raidarray).order_by(raidarray.headnode)
        if raidarrays is not None:
            for array in raidarrays:
                if array.headnode in self.headnodeidmap:
                    servername = self.headnodeidmap[array.headnode]
                    arrayname = array.name
                    self.raidarraysidmap[array.id] = array.name
                    self.status_tree[servername]['raidarrays'][arrayname] = {'attributes':array.returnImportantProperties(),'disks':{},'sparedisks':{}}

    def getJBODS(self):
        jbods = self.session.query(jbod).order_by(jbod.headnode, jbod.serialnumber)
        if jbods is not None:
            for chassis in jbods:
                if chassis.headnode in self.headnodeidmap:
                    servername = self.headnodeidmap[chassis.headnode]
                    self.jbodidmap[chassis.id] = chassis.serialnumber
                    self.status_tree[servername]['jbods'][chassis.serialnumber] = {'disks':{},'attributes':{}}
                    self.status_tree[servername]['jbods'][chassis.serialnumber]['attributes'] = chassis.returnImportantProperties()
        # self.session.expunge_all()


    def getharddrives(self):
        harddrives = self.session.query(harddrive).order_by(harddrive.jbod, harddrive.index)
        if harddrives is not None:
            for disk in harddrives:
                if disk.jbod in self.jbodidmap and disk.headnode in self.headnodeidmap:
                    jbodserial = self.jbodidmap[disk.jbod]
                    servername = self.headnodeidmap[disk.headnode]
                    self.harddrivesidmap[disk.id] = {'index':disk.index,'servername':servername,'jbodserial':jbodserial,'raidarrayname':None,'raidarrayrole':None,'israidspare':None}
                    self.status_tree[servername]['jbods'][jbodserial]['disks'][disk.index] = {'attributes':disk.returnImportantProperties(),'logicaldisks':{}}
                    # if disk.raidarray in self.raidarraysidmap:
                    #     arrayname = self.raidarraysidmap[disk.raidarray]
                    #     self.status_tree[servername]['raidarrays'][arrayname]['disks'].append(disk)
                        # raidarrayrole = disk.raidarrayrole
                        # if raidarrayrole > 1000:
                        #     raidarrayrole = int(raidarrayrole) - 1000
                        #     self.status_tree[servername]['raidarrays'][arrayname]['sparedisks'][raidarrayrole] = {'attributes':disk.returnImportantProperties(),'logicaldisks':{}}
                        #     self.harddrivesidmap[disk.id]['israidspare'] = True
                        #     self.harddrivesidmap[disk.id]['raidarrayname'] = arrayname
                        #     self.harddrivesidmap[disk.id]['raidarrayrole'] = raidarrayrole
                        # else:
                        #     self.status_tree[servername]['raidarrays'][arrayname]['disks'][raidarrayrole] = {'attributes':disk.returnImportantProperties(),'logicaldisks':{}}
                        #     self.harddrivesidmap[disk.id]['israidspare'] = False
                        #     self.harddrivesidmap[disk.id]['raidarrayname'] = arrayname
                        #     self.harddrivesidmap[disk.id]['raidarrayrole'] = raidarrayrole

        # self.session.expunge_all()

    def getLogicalDisks(self):
        logicaldisks = self.session.query(logicaldisk).order_by(logicaldisk.harddrive)
        if logicaldisks is not None:
            for ld in logicaldisks:
                if ld.harddrive in self.harddrivesidmap:
                    jbodserial = self.harddrivesidmap[ld.harddrive]['jbodserial']
                    servername = self.harddrivesidmap[ld.harddrive]['servername']
                    index = self.harddrivesidmap[ld.harddrive]['index']
                    self.status_tree[servername]['jbods'][jbodserial]['disks'][index]['logicaldisks'][ld.name] = {'attributes':ld.returnImportantProperties()}
                    # if self.harddrivesidmap[ld.harddrive]['israidspare'] is not None:
                    #     arrayname = self.harddrivesidmap[ld.harddrive]['raidarrayname']
                    #     arrayrole = self.harddrivesidmap[ld.harddrive]['raidarrayrole']
                    #     israidspare = self.harddrivesidmap[ld.harddrive]['israidspare']
                    #     if israidspare:
                    #         self.status_tree[servername]['raidarrays'][arrayname]['sparedisks'][arrayrole]['logicaldisks'][ld.name] = {'attributes':ld.returnImportantProperties()}
                    #     else:
                    #         self.status_tree[servername]['raidarrays'][arrayname]['disks'][arrayrole]['logicaldisks'][ld.name] = {'attributes':ld.returnImportantProperties()}



    def debug_print(self):
        pprint(self.status_tree)
