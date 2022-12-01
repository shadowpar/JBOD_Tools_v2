from .scsiOperations import scsiAddr2Model, sortSCSIDisks, getMountMap, scsiAddr2SG, scsiAddr2BlockDevName
from .scsiOperations import multiExecute, getMDparent, generateSAS2SerialMap
from hancockStorageMonitor.common.staticdatastorage import NEWJBODMODELS
from hancockStorageMonitor.localgatherers.virtualDevs import storage_md_raid, storage_lv, storage_dm_partition, storage_multipath_disk
from hancockStorageMonitor.localgatherers.virtualDevOps import mdadmScan, inventoryDeviceMapper, zfsscanner
from hancockStorageMonitor.localgatherers.physicalDevs import storage_jbod_old, storage_jbod_new, storage_physical_disk, storage_logical_disk
from hancockStorageMonitor.localgatherers.serverInfo import serverInfo
from platform import node
from pathlib import Path
import json
from datetime import datetime

class storage_info(object):
    def __init__(self):
        super(storage_info, self).__init__()
        self.sesController2modelMap = {}
        self.name2type = {}
        self.jbod_objects = {}
        self.harddrivesByChassis = {}
        self.logicalDisksByChassisEnclosure = {}
        self.raidarrays = {}
        self.zpools = {}
        self.dm_partitions = {}
        self.disksByChassisEnclosure = sortSCSIDisks()
        self.serials = [serial for serial in self.disksByChassisEnclosure]
        self.disksas2serialmap = {chassisSerial:generateSAS2SerialMap(chassisSerial=chassisSerial,sortedDisks=self.disksByChassisEnclosure) for chassisSerial in self.serials}
        self.mountMap = getMountMap()
        self.this_server = serverInfo()
        if self.this_server.hasdmraid:
            mdscan = mdadmScan()
        else:
            mdscan = None
        if self.this_server.haszfs:
            zfsscan = zfsscanner()
        else:
            zfsscan = None
        dmDevsByType = inventoryDeviceMapper(sortbyname=True)
        if mdscan is not None: self.raidarrays = {name:storage_md_raid(uniqueID=name,mdscan=mdscan) for name in mdscan}
        for item in self.raidarrays:
            self.name2type[item] = 'raidarrays'
            self.name2type[self.raidarrays[item].attributes['uuid']] = 'raidarrays'
        if zfsscan is not None: self.zpools = {}
        for item in self.zpools:
            self.name2type[item] = 'zpools'
        self.multipaths = {name:storage_multipath_disk(uniqueID=name,dmInventory=dmDevsByType) for name in dmDevsByType['mpath']}
        for item in self.multipaths:
            self.name2type[item] = 'multipaths'
            self.name2type[self.multipaths[item].attributes['name']] = 'multipaths'
        self.lvs = {name:storage_lv(uniqueID=name,dmInventory=dmDevsByType) for name in dmDevsByType['lv']}
        for item in self.lvs:
            self.name2type[item] = 'logicalvolumes'
            self.name2type[self.lvs[item].attributes['name']] = 'logicalvolumes'
        self.dm_partitions = {name:storage_dm_partition(uniqueID=name,dmInventory=dmDevsByType) for name in dmDevsByType['partition']}
        for item in self.dm_partitions:
            self.name2type[item] = 'raidpartitions'
            self.name2type[self.dm_partitions[item].attributes['name']] = 'raidpartitions'
        self.createLogicalDisks()
        for chassisSerial in self.serials:
            for encl in self.disksByChassisEnclosure[chassisSerial]:
                self.sesController2modelMap[encl] = scsiAddr2Model(encl)
        for chassisSerial in self.disksByChassisEnclosure:#loop over physical enclosures identified by chassisSerial number.
            chassis_encls = list(self.disksByChassisEnclosure[chassisSerial].keys())#  create a list of SCSI addresses of SES controllers.
            if self.sesController2modelMap[chassis_encls[0]] in NEWJBODMODELS:
                self.jbod_objects[chassisSerial] =  storage_jbod_new(uniqueID=chassisSerial, sesControllers=chassis_encls)
            else:
                self.jbod_objects[chassisSerial] = storage_jbod_old(uniqueID=chassisSerial, sesControllers=chassis_encls,disksByEnclosure=self.disksByChassisEnclosure[chassisSerial],
                                                             disksas2serial=self.disksas2serialmap[chassisSerial])
            self.name2type[chassisSerial] = 'jbods'
        self.createharddrives()

    def __repr__(self):
        response = str(type(self))
        for ra in self.raidarrays:
            response = response+"\n"+str(self.raidarrays[ra])
        for mp in self.multipaths:
            response = response+"\n"+str(self.multipaths[mp])
        for lv in self.lvs:
            response = response+"\n"+str(self.lvs[lv])
        for part in self.dm_partitions:
            response = response+"\n"+str(self.dm_partitions[part])
        for jb in self.jbod_objects:
            response = response+"\n"+str(self.jbod_objects[jb])
        return response

    def createLogicalDisks(self):
        for chassisSerial in self.disksByChassisEnclosure:
            self.logicalDisksByChassisEnclosure[chassisSerial] = {}
            for ses in self.disksByChassisEnclosure[chassisSerial]:
                sesSG = scsiAddr2SG(ses)
                self.name2type[ses] = 'sescontrollers'
                self.name2type[sesSG] = 'sescontrollers'
                self.logicalDisksByChassisEnclosure[chassisSerial][sesSG] = []
                argset = []
                for disk in self.disksByChassisEnclosure[chassisSerial][ses]:
                    scsiAddr = disk.name
                    sdname = scsiAddr2BlockDevName(scsiaddr=scsiAddr)[1]
                    argset.append({'sdname':sdname})
                    self.name2type[sdname] = 'logicaldisks'
                results = multiExecute(functionName=storage_logical_disk,kwargs=argset)
                values = list(results.values())
                self.logicalDisksByChassisEnclosure[chassisSerial][sesSG] = values

    def createharddrives(self):
        for chassisSerial in self.logicalDisksByChassisEnclosure:
            serial2slotmap = self.jbod_objects[chassisSerial].serial2slotMap
            self.harddrivesByChassis[chassisSerial] = {}
            for ses in self.logicalDisksByChassisEnclosure[chassisSerial]:
                harddrives = []
                alreadyExists = []
                for logicaldisk in self.logicalDisksByChassisEnclosure[chassisSerial][ses]:
                    diskserial = logicaldisk.attributes['serialnumber']
                    diskname = logicaldisk.attributes['uniqueID']
                    index = None
                    slot = None
                    if diskserial not in self.harddrivesByChassis[chassisSerial]:
                        if diskserial in serial2slotmap:
                            try:
                                index = serial2slotmap[diskserial]['index']
                                slot = serial2slotmap[diskserial]['slot']
                            except KeyError:
                                print("Disk with serial",diskserial,"is missing slot and index info.")
                        else:
                            print("disk with name",diskname,"and apparent serial",diskserial,"does not he a corresponding slot")
                            with open("/var/log/storageMonitor/storage_info.log",'a') as f:
                                f.write("problems with this disk intefered with collections: "+str(diskname)+"\n")
                            exit(1)
                        diskinfo ={'serialnumber':diskserial,'alogicaldisk':diskname,'slot':slot,'index':index,'nosmart':False}
                        self.name2type[diskserial] = 'harddrives'
                        harddrives.append(diskinfo)
                    else:
                        alreadyExists.append(logicaldisk)
                results = multiExecute(functionName=storage_physical_disk,kwargs=harddrives)
                values = [item for item in list(results.values())]

                self.harddrivesByChassis[chassisSerial].update({item.attributes['serialnumber']:item for item in values if item is not None})
                for item in alreadyExists:
                    theSerial = item.attributes['serialnumber']
                    if theSerial in self.harddrivesByChassis[chassisSerial]:
                        self.harddrivesByChassis[chassisSerial][theSerial].addChild(item.attributes['uniqueID'])

    def exportDictionary(self,write=True):
        data = {'json_format_version':'1.0','modified':datetime.timestamp(datetime.utcnow()),
                'headnodes':self.this_server.exportDictionary(),
                'raidarrays':{array.attributes['uuid']:array.exportDictionary(properties={'hostname':self.this_server.name}) for array in self.raidarrays.values()},
                'jbods':{jbod.attributes['serialnumber']:jbod.exportDictionary(properties={'hostname':self.this_server.name}) for jbod in self.jbod_objects.values()},
                'harddrives':{}}
        data['cpus'] = data['headnodes']['cpu_data']
        data['headnodes'].pop('cpu_data')
        for key in self.mountMap:
            self.mountMap[key].update({'hostname':self.this_server.name})
        data['mounts'] = self.mountMap
        if self.this_server.haszfs and len(self.raidarrays) == 0:
            data['headnodes'][self.this_server.name]['raidtype'] = 'zfs'
        elif self.this_server.hasdmraid and len(self.raidarrays) > 0:
            data['headnodes'][self.this_server.name]['raidtype'] = 'mdraid'
        else:
            data['headnodes'][self.this_server.name]['raidtype'] = None
        for chassisSerial in self.harddrivesByChassis:
            for disk in self.harddrivesByChassis[chassisSerial]:
                searchkey = disk
                firstLogical = self.harddrivesByChassis[chassisSerial][disk].attributes['children'][0]
                mdparent = getMDparent(blockName=firstLogical)
                if mdparent is None:
                    mdparentuuid = None
                else:
                    mdparentuuid = self.raidarrays[mdparent].attributes['uuid']
                data['harddrives'][searchkey] = self.harddrivesByChassis[chassisSerial][searchkey].exportDictionary(properties={'chassisSerial':chassisSerial,'hostname':self.this_server.name,
                                                                                                                                'mdparent':mdparentuuid})
        json.dumps(data['harddrives'])
        data['logicaldisks'] = {}
        for chassisSerial in self.logicalDisksByChassisEnclosure:
            for encl in self.logicalDisksByChassisEnclosure[chassisSerial]:
                for logdisk in self.logicalDisksByChassisEnclosure[chassisSerial][encl]:
                    searchkey = logdisk.attributes['uniqueID']
                    data['logicaldisks'][searchkey] = logdisk.exportDictionary(properties={'chassisSerial':chassisSerial,'enclosure':encl,'hostname':self.this_server.name})
        json.dumps(data['logicaldisks'])
        export_path = Path('/tmp').joinpath(str(node())+'_storageMonitor.dat')
        if write:
            with export_path.open('w') as f:
                json.dump(data,f)

        return data




