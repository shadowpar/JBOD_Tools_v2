from pathlib import Path
from hancockStorageMonitor.localgatherers.procFSoperations import parseProcDevices, parseProcPartitions
from os import getuid
from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand
from os import readlink

def getAllMultipathDevices():
    pass

def getMultipathParents(scsiaddrChildren=[]):
    if len(scsiaddrChildren) == 0:
        print("This function expects a list of SCSI addresses in a string format.")
        return None

def getMultipathParent(scsiaddr):
    sdPath = Path('/sys/bus/scsi/drivers/sd')
    allSD = [item.name for item in sdPath.iterdir() if item.is_symlink()]
    if scsiaddr not in allSD:
        print("This does not appear to be a SCSI disk on the system.")
        return None

#  This will return the type of block devices from the list ['sd','sdpartition','mpath','mpathpartition','md','mdpartition','nvme','nvmepartion,'lv','lvpartition]
#  The primary use of this function to to identify the type of a device listed as parent or child of another device in /sys/block/deviceName/holders or /slaves
# you can optionally pase in the results of parseProcDevices and parseProcPartions if you will call this function repeatedly.
def checkBlockDevType(name=None, knownDeviceDrivers=parseProcDevices(),knownBlockDevices=parseProcPartitions(inverse=True)):
    if 'block' in knownDeviceDrivers.keys():
        knownDeviceDrivers = knownDeviceDrivers['block']
    if name is None or type(name) != str:
        print("Please pass an identifier for the block device as a string. These identifiers are like sda, sdb1, nvme0n1, nvme0n1p1, dm-98 found in /dev")
        return None
    elif '/' in name:
        print("Only pass in the name of the device not the full path, i.e. sdie, not /dev/sdie, or /sys/block/sdie")
        return None
    blockDevPath = Path('/dev').joinpath(name)
    if not blockDevPath.is_block_device():
        print(name," is not a block device on this system.")
        return None
    if name in knownBlockDevices:
        major, minor = knownBlockDevices[name]['major'], knownBlockDevices[name]['minor']
    else:
        print("Unable to locate the major and minor numbers for  device",name)
        return None
    sysBlockPath = Path('/sys/dev/block/').joinpath(major+':'+minor)
    if knownDeviceDrivers[major].lower() == 'sd':
        #  Two methods of differentiation of devices with sd driver. THe first is more robust and preferred.
        if sysBlockPath.joinpath('uevent').is_file():
            ueventPath = sysBlockPath.joinpath('uevent').read_text().splitlines()
            attrs = {line.split('=')[0].lower():line.split('=')[1].lower() for line in ueventPath if len(line.split("=")) == 2}
            if 'devtype' in attrs.keys():
                return {'partition':'sdpartition','disk':'sd'}[attrs['devtype']]
        #In the case that uevent file does not contain the information we use, there is an alternate method below.
        nonParts = [item.name for item in Path('/sys/block').glob("sd*") if item.is_symlink()]
        if name in nonParts:
            return 'sd'
        else:
            return 'sdpartition'
    elif knownDeviceDrivers[major].lower() == 'device-mapper':
        devPath = Path('/sys/dev/block').joinpath(major+':'+minor)
        uuid = devPath.joinpath('dm').joinpath('uuid').read_text()
        uuidMain = uuid.split('-')[0]
        uuidSecond = uuid.split("-")[1]
        if 'LVM' in uuidMain:
            return 'lv'
        elif 'part' in uuidMain:
            if 'LVM' in uuidSecond:
                return 'lvpartition'
            elif 'mpath' in uuidSecond:
                return 'mpathpartition'
            elif 'md' in uuidSecond:
                return 'mdpartition'
            else:
                return 'partition'
        elif 'mpath' in uuidMain:
            return 'mpath'
        else:
            return None
    elif knownDeviceDrivers[major].lower() == 'md':
        devPath = Path('/sys/dev/block').joinpath(major+':'+minor)
        if devPath.joinpath('md').is_dir():
            return 'md'
        else:
            mdScanInfo = mdadmScan()
            if name in mdScanInfo:
                return 'md'
        print("This is an unknown device using the md device driver.")
        return None

#  Inventories and sorts all devices using the device-mapper (dm) driver. This includes logical volumes (lvs),
#  multipath devices (mpaths), and the partitions  that sit atop either of these virtual devices.
def inventoryDeviceMapper(sortbyname=False):
    dmDeviceByType = {'partition':{},'mpath':{},'lv':{}}
    virtualBlockPath = Path('/sys/devices/virtual/block/')
    if virtualBlockPath.is_dir():
        dmDevs = [item for item in list(virtualBlockPath.iterdir()) if item.joinpath('dm').is_dir()]
    else:
        dmDevs = []

    for dmDev in dmDevs:
        name = dmDev.joinpath('dm').joinpath('name').read_text().strip()
        uuid = dmDev.joinpath('dm').joinpath('uuid').read_text().strip()
        fullpath = dmDev.resolve()
        dmname = dmDev.name
        fields = uuid.split('-')
        if sortbyname:
            selector = dmname
        else:
            selector = uuid
        attributes = {'uuid':uuid,'dmname':dmname,'name':name,'fullpath':fullpath}
        if 'LVM' in fields[0]:
            dmDeviceByType['lv'][selector] = attributes.copy()
            dmDeviceByType['lv'][selector].update({'dmType':'lv'})
        elif 'mpath' in fields[0]:
            dmDeviceByType['mpath'][selector] = attributes.copy()
            dmDeviceByType['mpath'][selector].update({'dmType':'mpath'})
        elif 'part' in fields[0]:
            dmDeviceByType['partition'][selector] = attributes.copy()
            dmDeviceByType['partition'][selector].update({'dmType':'partition'})
    return dmDeviceByType

#  Inventories software RAID devices on the system.
def inventoryMD():
    virtualBlockPath = Path('/sys/devices/virtual/block')
    mdDevs = [item for item in list(virtualBlockPath.iterdir()) if item.joinpath('md').is_dir()]
    mdadmScanInfo = mdadmScan()
    if mdadmScanInfo is None:
        print("There is an issue with mdadm, cannot gather all info about MD devices.")
        return None
    mdInventory = {}
    for mdDev in mdDevs:
        name = mdDev.name
        mdInventory[name] = {'name':name}
        if mdDev.joinpath('dev').is_file():
            major, minor =  mdDev.joinpath('dev').read_text().strip().split(":")
            mdInventory[name]['major'] = major
            mdInventory[name]['minor'] = minor
        if name in mdadmScanInfo:
            mdInventory[name].update(mdadmScanInfo[name])
        mddetail = getMDdetails(mdname=name)
        if mddetail is not None:
            mdInventory[name].update(mddetail)
    return mdInventory

def zfsscanner():
    if getuid() != 0:
        print("The function must be run as the root user.")
        return None
    command = ['zpool','status']
    result = errorHandledRunCommand(command=command,timeout=30)
    # proc = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
    if result['returncode'] > 0:
        return None
def mdadmScan():
    if getuid() != 0:
        print("The function must be run as the root user.")
        return None
    command = ['mdadm','-D','--scan']
    result = errorHandledRunCommand(command=command,timeout=30)
    # proc = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
    if result['returncode'] > 0:
        return None

    output = result['stdout'].splitlines()
    mdInformation = {}
    for line in output:
        parts = line.split()
        if parts[0].lower() != 'array':
            continue
        else:
            attributes = parts[2:]
            # print(attributes)
            attributes = {attr.split("=")[0].lower():attr.split("=")[1] for attr in attributes if len(attr.split("=")) == 2 }
            # print(attributes)
            namedata = list(filter(None,parts[1].split('/')))
            # print(namedata)
            if len(namedata) == 2:# This is a hack to handle two different output formats of mdadm -D --scan the top one is like /dev/md3
                mdPath = Path('/').joinpath(namedata[0]).joinpath(namedata[1])
                # print(mdPath,"c1")
            elif len(namedata) == 3: # The bottom one (older) is /dev/3/md.
                if namedata[0] == 'dev' and namedata[1] == 'md':
                    # patch to allow functionality on ubuntu and similar. mdadm -D --scan output lists devices in /dev/md/md* friendly names.
                    friendlyLink = Path('/dev/md').joinpath(namedata[2])
                    if friendlyLink.is_symlink():
                        mdPath = Path(readlink(friendlyLink)).absolute()
                else:
                    mdPath = Path('/').joinpath(namedata[0]).joinpath(namedata[1]+namedata[2])
                # print(mdPath,"c2")

            else:
                raise Exception("Failed to understand output of mdadm -D --scan, please investigate mdadmScan() in virtualDevOps")
            mdInformation[mdPath.name] = attributes



    if len(mdInformation) == 0:
        # print("It appears there was a problem running mdadm -D --scan. See error output below.")
        # print(result['stderr'])
        return None
    return mdInformation

def getMDdetails(mdname=None):
    # mdInfoTargets is a dictionary that maps database property names to relative paths of files inside /sys/block/md*/
    # If there is a failure this function returns none, otherwise it returns a dictionary of looked up values.
    mdInfoTargets = {'chunksize':'chunk_size','componentsize':'component_size',
                   'degraded':'degraded','totalnumdisks':'raid_disks',
                   'lastsyncaction':'last_sync_action','mismatchcnt':'mismatch_cnt',
                   'syncspeed':'sync_speed','syncspeedmax':'sync_speed_max',
                   'syncspeedmin':'sync_speed_min','syncaction':'sync_action',
                    'stripecachesize':'stripe_cache_size','raidlevel':'level',
                     'consistencypolicy':'consistency_policy','arraystate':'array_state',
                     'metadataversion':'metadata_version'}
    returnData = {}
    if mdname is None:
        return None
    for item in mdInfoTargets:
        try:
            target = Path('/sys/block').joinpath(mdname).joinpath('md').joinpath(mdInfoTargets[item])
            if target.is_file():
                returnData[item] = target.read_text().strip()
            else:
                print("File not found",target.resolve())
        except Exception:
            print("An unhandled exception occured in getMDdetails.")
    if len(returnData) == 0:
        return None
    else:
        return returnData

def genArgStringFromDict(inputDict={}):
    output = ""
    for item in inputDict:
        output = output+str(item)+"="+str(inputDict[item])+","
    return None


