from hancockStorageMonitor.localgatherers.physicalDevs import storage_device
from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand, checkReadPropertyFile, getBlockImmediateChildren, getBlockImmediateParents, getMountMap
from hancockStorageMonitor.localgatherers.virtualDevOps import mdadmScan, inventoryDeviceMapper
from pathlib import Path
import json
# Virtual device classes.

class storage_md_raid(storage_device):
    def __init__(self,uniqueID,mdscan=None):
        super().__init__(uniqueID=uniqueID)
        self.name = self.attributes['name'] = uniqueID
        self.uuid = ''
        mountmap = getMountMap()
        if mdscan is None:
            self.mdscan = mdadmScan()
        else:
            self.mdscan = mdscan
        self.fullpath = self.attributes['fullpath'] = Path('/sys/devices/virtual/block').joinpath(self.name)
        self.getUUID()
        self.getSYSFSdetails()
        if self.name in getMountMap():
            self.attributes['mountpoint'] = mountmap[self.name]['mountpoint']
            self.attributes['filesystem'] = mountmap[self.name]['filesystem']
        else:
            self.attributes['mountpoint'] = None
            self.attributes['filesystem'] = None

    def getUUID(self):
        if self.name in self.mdscan:
            if 'bitmap' in self.mdscan[self.name]:
                self.attributes['bitmapfile'] = self.mdscan[self.name]['bitmap']
            else:
                self.attributes['bitmapfile'] = None
            if 'uuid' in self.mdscan[self.name]:
                self.uuid = self.attributes['uuid'] = self.mdscan[self.name]['uuid']
                return
            else:
                self.attributes['uuid'] = None
        else:
            self.attributes['bitmapfile'] = None
        diskByIDPath = Path('/dev/disk/by-id')
        possibleUUIDs = [item.name.lstrip('md-uuid-') for item in list(diskByIDPath.iterdir()) if 'md-uuid' in item.name and item.resolve().name == self.name]
        if len(possibleUUIDs) == 1:
            self.uuid = self.attributes['uuid'] = possibleUUIDs[0]
            return
        else:
            command = ['mdadm','-D','/dev/'+self.name,'--export']
            result = errorHandledRunCommand(command=command,timeout=30)
            if result is None or result['returncode']:
                self.uuid = self.attributes['uuid'] = None
                return
            else:
                output = result['stdout'].splitlines()
                uuid = [line.split('=')[1] for line in output if 'uuid' in line.lower()]
                if len(uuid) == 1:
                    self.uuid = self.attributes['uuid'] = uuid[0]
                else:
                    self.uuid = self.attributes['uuid'] = None

    def getSYSFSdetails(self):
        # print(self.name)
        # print(self.fullpath)
        majorMinor = checkReadPropertyFile(self.fullpath.joinpath('dev'))
        if majorMinor is not None:
            self.attributes['major'], self.attributes['minor'] = majorMinor.strip().split(':')
        mdPath = self.fullpath.joinpath('md')
        self.attributes['chunksize'] = checkReadPropertyFile(mdPath.joinpath('chunk_size'))
        self.attributes['componentsize'] = checkReadPropertyFile(mdPath.joinpath('component_size'))
        contents = checkReadPropertyFile(mdPath.joinpath('degraded'))
        try:
            self.attributes['degraded'] = bool(int(contents))
        except TypeError as t:
            print(t)
            self.attributes['degraded'] = False
        self.attributes['totalnumdisks'] = checkReadPropertyFile(mdPath.joinpath('raid_disks'))
        self.attributes['lastsyncaction'] = checkReadPropertyFile(mdPath.joinpath('last_sync_action'))
        self.attributes['mismatchcnt'] = checkReadPropertyFile(mdPath.joinpath('mismatch_cnt'))
        self.attributes['syncspeed'] = checkReadPropertyFile(mdPath.joinpath('sync_speed'))
        self.attributes['syncspeedmax'] = checkReadPropertyFile(mdPath.joinpath('sync_speed_max'))
        self.attributes['syncspeedmin'] = checkReadPropertyFile(mdPath.joinpath('sync_speed_min'))
        self.attributes['syncaction'] = checkReadPropertyFile(mdPath.joinpath('sync_action'))
        self.attributes['stripecachesize'] = checkReadPropertyFile(mdPath.joinpath('stripe_cache_size'))
        self.attributes['raidlevel'] = checkReadPropertyFile(mdPath.joinpath('level'))
        self.attributes['consistencypolicy'] = checkReadPropertyFile(mdPath.joinpath('consistency_policy'))
        self.attributes['arraystate'] = checkReadPropertyFile(mdPath.joinpath('array_state'))
        self.attributes['metadataversion'] = checkReadPropertyFile(mdPath.joinpath('metadata_version'))
        raidMemberPaths = [item for item in list(mdPath.iterdir()) if 'dev-' in item.name]
        self.attributes['members'] = {}
        for member in raidMemberPaths:
            name = member.joinpath('block').resolve().name
            raidslot = checkReadPropertyFile(member.joinpath('slot'))
            memberstate = checkReadPropertyFile(member.joinpath('state'))
            self.attributes['members'][name] = {'raidslot':raidslot,'memberstate':memberstate}


#  Abstract base class never meant to be instantiated.
class storage_dm_device(storage_device):
    def __init__(self,uniqueID,dmInventory=inventoryDeviceMapper(sortbyname=True),dmType=None):
        super().__init__(uniqueID=uniqueID)
        self.dmInventory = dmInventory
        self.attributes.update(self.dmInventory[dmType][uniqueID])
        self.children = self.attributes['children'] =  getBlockImmediateChildren(blockName=self.attributes['dmname'])
        self.parents = self.attributes['parents'] =  getBlockImmediateParents(blockName=self.attributes['dmname'])
        majorMinor = checkReadPropertyFile(self.attributes['fullpath'].joinpath('dev'))
        if majorMinor is not None:
            self.attributes['major'] , self.attributes['minor']  = majorMinor.strip().split(':')

#  This class represents a multipath device. Its constructor expects a uniqueID which should be the name assigned to it
#  by the dm driver. i.e. dm-34. While this is not globally unique, it is unique to the server. For global uniqueness we
#  use the UUID
class storage_multipath_disk(storage_dm_device):
    def __init__(self,uniqueID,dmInventory=inventoryDeviceMapper(sortbyname=True)):
        self.dmType = 'mpath'
        super().__init__(uniqueID=uniqueID,dmType=self.dmType)

class storage_lv(storage_dm_device):
    def __init__(self,uniqueID,dmInventory=inventoryDeviceMapper(sortbyname=True)):
        self.dmType = 'lv'
        super().__init__(uniqueID=uniqueID,dmType=self.dmType)

class storage_dm_partition(storage_dm_device):
    def __init__(self,uniqueID,dmInventory=inventoryDeviceMapper(sortbyname=True)):
        self.dmType = 'partition'
        super().__init__(uniqueID=uniqueID,dmType=self.dmType)









