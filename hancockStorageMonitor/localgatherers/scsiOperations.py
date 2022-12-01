#  from string import digits as DIGITS
import statistics
import subprocess
from os import getuid
from pathlib import Path, PosixPath
import json
import concurrent.futures
from os import environ
import traceback
import asyncio
from os import readlink
from time import perf_counter

def getMountMap():
    mountDict = {}
    mountPath = Path('/proc/mounts')
    mountData = mountPath.read_text().splitlines()
    for line in mountData:
        parts = line.split()
        dev = Path(parts[0].strip())
        if dev.is_block_device():
            if dev.is_symlink():
                alternate = dev.name
                name = Path(readlink(dev)).name
            else:
                alternate = None
                name = dev.name

            mp = Path(parts[1].strip())
            fs = str(parts[2].strip())
            mountDict[name] = {'mountpoint':mp.as_posix(),'name':name,'filesystem':fs,'alternatename':alternate}
    return mountDict

def getBlockImmediateChildren(scsiaddr=None,blockName=None):
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    children = blockPath.joinpath('slaves')
    if children.is_dir():
        children = [item.name for item in list(children.iterdir()) if item.is_symlink()]
    else:
        return None
    children.sort()
    return children

def getBlockImmediateParents(scsiaddr=None,blockName=None):
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    parents = blockPath.joinpath('holders')
    if parents.is_dir():
        parents = [item.name for item in list(parents.iterdir()) if item.is_symlink()]
    else:
        return None
    return parents

#  This function returns the OTHER devices that share this devices parent. i.e. have a common occupant of the sysfs 'holders' directory.
#  The mpathonly parameter should be set to True if you only want siblings when the parent is a multipath device.
def getBlockSiblings(scsiaddr=None,blockName=None):
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    parents = getBlockImmediateParents(blockName=blockPath.name)
    siblings = []
    if parents is not None:
        for parent in parents:
            myChildren = getBlockImmediateChildren(blockName=parent)
            if myChildren is not None:
                for child in myChildren:
                    if child not in siblings and child != blockPath.name:
                        siblings.append(child)
            else:
                print("Something is wrong here. This parent should have at least one child. me.")
                return None
    else:
        print("No parents, no siblings")
        return None
    if not siblings:
        return None
    else:
        return siblings

def readMajorMinor(devPath):
    if type(devPath) == PosixPath:
        try:
            major, minor = devPath.joinpath('dev').read_text().strip().split(':')
            return {'major':major,'minor':minor}
        except Exception:
            print("Failed to get major and minor numbers")
            return None
    else:
        print("The type of object passed is",type(devPath))
        print("You must pass this function an object of type pathlib.Path")
        return None

def scsiAddr2SerialNumber(scsiaddr=None):
    if getuid() != 0:
        print("This function requires root access.")
        return None
    if scsiaddr is None:
        print("Please pass in SCSI address as the first parameter.")
    sgname = scsiAddr2SG(scsiaddr)
    if sgname is None:
        print("Unable to find the SCSI generic interface for SCSI device with address",scsiaddr)
        return None
    else:
        command = ['sg_vpd','-p','sn','-q',Path('/dev/').joinpath(sgname).as_posix()]
        results = errorHandledRunCommand(command=command,timeout=60)
        if results is None or results['returncode'] != 0:
            print("Error trying to get serial number for SCSI device",scsiaddr)
            return None
        else:
            return results['stdout'].split()[-1]

async def scsiAddr2SerialNumberAsync(scsiaddr=None):
    if getuid() != 0:
        print("This function requires root access.")
        return None
    if scsiaddr is None:
        print("Please pass in SCSI address as the first parameter.")
    sgname = scsiAddr2SG(scsiaddr)
    if sgname is None:
        print("Unable to find the SCSI generic interface for SCSI device with address",scsiaddr)
        return (scsiaddr,None)
    else:
        command = ['sg_vpd','-p','sn','-q',Path('/dev/').joinpath(sgname).as_posix()]
        commandString = ''
        for item in command:
            commandString = commandString+' '+str(item)
        c, outcome = await errorHandledRunCommandaAsync(command=commandString, timeout=60)
        if outcome is None:
            print("Error trying to get serial number for SCSI device",scsiaddr)
            return (scsiaddr,outcome)
        if outcome['returncode'] != 0:
            print("Error trying to get serial number for SCSI device",scsiaddr)
            return (scsiaddr,outcome)
        else:
            return (scsiaddr,outcome['stdout'].split()[-1])

def blockDevName2SerialNumber(blockName=None):
    if getuid() != 0:
        print("This function requires root access.")
        return None
    if blockName is None:
        print("Please pass in block name as the first parameter.")
        return None
    command = ['sg_vpd','-p','sn','-q',Path('/dev/').joinpath(str(blockName)).as_posix()]
    results = errorHandledRunCommand(command=command,timeout=90)
    if results is None or results['returncode'] != 0:
        print("Error trying to get serial number for block device",blockName)
        return None
    else:
        return results['stdout'].split()[-1]

async def blockDevName2SerialNumberAsync(blockName):
    if getuid() != 0:
        print("This function requires root access.")
        return None
    if blockName is None or not Path('/dev').joinpath(blockName).is_block_device():
        print("Please pass in SCSI address as the first parameter.")
        return (blockName,None)

    command = ['sg_vpd','-p','sn','-q',Path('/dev/').joinpath(blockName).as_posix()]
    commandString = ''
    for item in command:
        commandString = commandString+' '+str(item)
    c, outcome = await errorHandledRunCommandaAsync(command=commandString, timeout=60)
    if outcome is None:
        print("Error trying to get serial number for SCSI device",blockName)
        return (blockName,outcome)
    if outcome['returncode'] != 0:
        print("Error trying to get serial number for SCSI device",blockName)
        return (blockName,outcome)
    else:
        print("inside blockdevname2serialnumberAsync I am about to return")
        print(blockName,outcome['stdout'].split()[-1])
        return (blockName,outcome['stdout'].split()[-1])

#This function sorts the SCSI devices found on system according to there SCSI type
#The three types currently implemented are '12'=hw raid controller, '13'=SES controller, '0'=disk
#  If the sesOnly parameter is set to True, this function will only return results for SCSI enclosure services devices.
def sortSCSI(sesOnly=False):
    scsiBusSESPath = Path('/sys/bus/scsi/drivers/ses')
    scsiBusSDPath = Path('/sys/bus/scsi/drivers/sd')
    if scsiBusSESPath.is_dir():
        scsiSESPaths = [item for item in list(scsiBusSESPath.iterdir()) if item.is_symlink()]
    else:
        scsiSESPaths = []
    if not sesOnly:
        if scsiBusSDPath.is_dir():
            scsiSDSPaths = [item for item in list(scsiBusSDPath.iterdir()) if item.is_symlink()]
        else:
            scsiSDSPaths = []
        scsiDevicesByType = {'12':[],'13':[],'0':[]}
        for dev in scsiSDSPaths:
            typePath = dev.joinpath('type')
            if typePath.is_file():
                scsiType = typePath.read_text().strip()
            else:
                continue
            try:
                scsiDevicesByType[scsiType].append(dev.resolve())
            except KeyError as k:
                print(k)
                print("Type ", scsiType, "is not known. Ignoring device", str(dev))
    else:
        scsiDevicesByType = {'13':[]}

    for dev in scsiSESPaths:
        typePath = dev.joinpath('type')
        if typePath.is_file():
            scsiType = typePath.read_text().strip()
        else:
            continue
        try:
            scsiDevicesByType[scsiType].append(dev.resolve())
        except KeyError as k:
            print(k)
            print("Type ",scsiType,"is not known. Ignoring device",str(dev))

    return scsiDevicesByType

#This function takes the full pci path in /sys/devices to a JBOD SES controller.
#It returns the pci path to the closest (usually t1) expander inside the JBOD
#It is used because this expander path is compared to the first full path for each disk
#to determine which physical chassis the disk is installed in.
def getLastExpanderFullPath(scsiaddr=None):
    if scsiaddr is None:
        print("No scsi address provided.")
    scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr)
    if not scsiPath.is_symlink():
        print("Not a valid SCSI address")
        return None
    sesFullPath = scsiPath.resolve()
    t1expander = None
    for item in sesFullPath.parts:
        if 'expander' in item:
            t1expander = item
    if t1expander is None:
        print("Failed to locate an expander. Returning None.")
        return None
    t1Path = Path("")
    for part in sesFullPath.parts:
        t1Path = t1Path.joinpath(part)
        if part == t1expander:
            break
    return t1Path


#this function takes a scsi address and returns the SCSI generic interface device name.
def scsiAddr2SG(scsiaddr=None):
    if scsiaddr is None or type(scsiaddr) != str:
        print("This function requires a SCSI address formatted as a string.")
        return None
    try:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr)
        fullPath = scsiPath.resolve()
        genericPath = fullPath.joinpath('scsi_generic')
        if genericPath.is_dir():
            genericList = list(genericPath.iterdir())
            if len(genericList) > 0:
                sgName = genericList[0].name
                return str(sgName)
            else:
               print("This scsi device has no corresponding b device.")
               return None
        else:
            print("This scsi device has no corresponding scsi generic name, or it doesn't exist.")
            return None
    except FileNotFoundError as e:
        print(e)
        print("Unable to locate scsi device with address",scsiaddr)
        return None

#  This function takes the generic SCSI name like sg1 and returns the SCSI address.
def sg2SCSIaddr(sgname=None):
    if sgname is None:
        print("This function expects a generic SCSI name such as sg1")
        return None
    sgPath = Path('/sys/class/scsi_generic').joinpath(sgname)
    if not sgPath.is_symlink():
        print("A generic SCSI device named",sgname,"was not found on this system.")
        return None
    fullpath = sgPath.joinpath('device').resolve()
    scsiaddr = fullpath.name
    return scsiaddr
#  Given the SCSI address of a device that is also a block device, return the kernel block device name.
def scsiAddr2BlockDevName(scsiaddr=None):
    if scsiaddr is None:
        return (scsiaddr,None)
    try:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr)
        fullPath = scsiPath.resolve()
        blockPath = fullPath.joinpath('block')
        if blockPath.is_dir():
            blockList = list(blockPath.iterdir())
            if len(blockList) > 0:
                blockName = blockList[0].name
                return (scsiaddr, str(blockName))
            else:
                print("This scsi device has no corresponding block device.")
                return (scsiaddr,None)
        else:
            print("This scsi device has no corresponding block device.")
            return (scsiaddr,None)
    except FileNotFoundError as e:
        print(e)
        print("Unable to locate scsi device with address",scsiaddr)
        return (scsiaddr,None)


def blockDevName2SCSIaddr(blockDevName=None):
    devPath = Path('/dev').joinpath(blockDevName)
    if blockDevName is None or not devPath.is_block_device():
        print("This function expects a blockdev name like sda")
        return None
    blockDevPath = Path('/sys/block').joinpath(blockDevName)
    scsiDevicePath = blockDevPath.joinpath('device')
    # scsiaddr = scsiDevicePath.resolve().name
    try:
        scsiaddr = Path(readlink(scsiDevicePath)).name
    except Exception as e:
        print(e)
        scsiaddr = None
    return scsiaddr


def scsiAddr2FullPath(scsiaddr=None):
    if scsiaddr is None:
        return None
    scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr)
    if scsiPath.is_symlink():
        fullPath = scsiPath.resolve()
        return fullPath
    else:
        print("Unable to locate the SCSI device with address",scsiaddr)
        return None

def scsiAddr2SASaddr(scsiaddr=None):
    if scsiaddr is None:
        print("This function expects a SCSI address like 1:5:6:0")
        return (scsiaddr,None)
    scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr)
    if scsiPath.is_symlink():
        endDevicePath = scsiAddr2EndDevice(scsiaddr=scsiaddr)
        if endDevicePath is None:
            return (scsiaddr,None)
        endDevicePath = endDevicePath.joinpath('sas_device')
        if endDevicePath.is_dir():
            contents = list(endDevicePath.iterdir())
            if len(contents) != 1:
                print("I don't know which to grab!!!")
                return (scsiaddr,None)
            else:
                sasAddressPath = contents[0].joinpath('sas_address')
                if sasAddressPath.is_file():
                    sasAddress = sasAddressPath.read_text().strip().lstrip('0x')
                    return (scsiaddr,sasAddress)
                else:
                    print("Cannot file sas address file in sas end device")
                    return (scsiaddr,None)
        else:
            print("I cannot find the end device when trying to get SAS address")
            return (scsiaddr,None)
    else:
        print("Unable to locate the SCSI device with address",scsiaddr)
        return (scsiaddr,None)

def blockDevName2SASaddr(blockName=None):
    if blockName is None:
        print("This function expects a block device name")
        return None
    blockPath = Path('/sys/block').joinpath(blockName)
    if not blockPath.is_dir():
        print("Unable to find the block device",blockName)
        return None
    sasaddressPath = blockPath.joinpath('device').joinpath('sas_address')
    if sasaddressPath.is_file():
        sasaddress = sasaddressPath.read_text().lstrip('0x').strip()
        return sasaddress
    else:
        print("Unable to find sas address for block device",blockName)



#  This function returns a list of SCSI addresses that map to the SAS address. There can be multiple results because each
#  disk chassis is an independant SAS domain. It is up the the caller to differentiate between disks if multiple disk
#  have the same SAS address. You can use the scsiDisk2SEScontroller() function to help differentiate. Alternatively,
#  this function will differentiate for you if you pass in the optional scsiAddrSESController parameter. This is the SCSI address
#  of the SES controller that handles the disk in question. The next optional parameter is a dictionary produced by the
#  scsiAddrs2SASaddrsMap() function of the form {scsiaddr:sasaddr} for all SCSI devices on the system. use this parameter
#  if you are calling sasAddr2SCSIaddr repeatedly, it is much more efficient. Same with sesControllerMap produced by
#  getSEScontrollerMap().
def sasAddr2SCSIaddr(sasaddr=None,scsiAddrSESController=None,sasDictionary=None,sesControllerMap=None):
    if sasaddr is None:
        print("This function expects a SAS address string like 5000c500869ee12e")
    sasaddr = sasaddr.lstrip('0x')
    #  First we try the more efficient method. That is look in /dev/disk/by-path and see if we can find the SAS address
    #  tied to a device.
    diskByPath = Path('/dev/disk/by-path')
    diskByPathWithSAS = [item.resolve().name for item in list(diskByPath.iterdir()) if 'part' not in item.name.lower() and sasaddr in item.name.lower()]
    scsiaddrs = []
    for item in diskByPathWithSAS:
        scsiForName = blockDevName2SCSIaddr(item)
        if scsiForName is not None:
            scsiaddrs.append(scsiForName)
    #  --------------------------------------------------------------------------------------------------------------------
    #  If the first method failed, then we must generate a list of the SAS addresses of all scsi disks use it for lookup.
    #  Since the SAS domains can overlap with multiple disk chassis, we also return the SES controller associated with the SCSI disk.
    #  This allows the caller to resolve ambiguity when multiple disks share the same SAS address in differnet disk chassis.
    if len(scsiaddrs) == 0:
        if sasDictionary is None:
            sasDictionary = scsiAddrs2SASaddrsMap()
        scsiaddrs = [key for key in sasDictionary if sasDictionary[key] == sasaddr]
    if scsiAddrSESController is None:
        return scsiaddrs
    else:
        #  Here we check the SES controller of each SCSI address to determine which one matches the given SEScontroller
        sesPath = Path('/sys/bus/scsi/drivers/ses')
        if scsiAddrSESController in [item.name for item in list(sesPath.iterdir())]:
            for diskSCSIAddr in scsiaddrs:
                deviceSEScontroller = scsiDisk2SEScontroller(diskSCSIAddr,sesControllerMap=sesControllerMap)
                if deviceSEScontroller == scsiAddrSESController:
                    return [diskSCSIAddr]
            #  If the user specified an SES controller AND none of the are attached to it, return None
            print("No disks with this SAS address",sasaddr,"is attached to the given SES controller.")
            return None
        #  If the SES controller that is given is not valid, we return all SCSI addresses matching the SAS address.
        else:
            print("The SCSI address",scsiAddrSESController,"does not correspond to an SES controller on this system.")
            return scsiaddrs

def scsiAddrs2SASaddrsMap():
    scsiPath = [item.resolve().name for item in list(Path('/sys/class/scsi_device').iterdir()) if item.is_symlink()]
    sasDictionary = {item:scsiAddr2SASaddr(scsiaddr=item)[1] for item in scsiPath if scsiAddr2SASaddr(scsiaddr=item)[1] is not None}
    return sasDictionary

def scsiAddr2EndDevice(scsiaddr=None):
    if scsiaddr is None:
        return None
    scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr)
    if scsiPath.is_symlink():
        fullPath = scsiPath.resolve()
        endDevice = None
        for item in fullPath.parts:
            if 'end_device' in item:
                endDevice = item
        if endDevice is None:
            # print("end device not found in scsiAddr2EndDevice")
            return None
        endDevicePath = Path("")
        for item in fullPath.parts:
            endDevicePath = endDevicePath.joinpath(item)
            if item == endDevice:
                break
        return endDevicePath
    else:
        print("Unable to locate the SCSI device with address",scsiaddr)
        return None
#  This function generates a dictionary that maps the full path of the tier 1 expanders in connected JBODs to the
#  SCSI address of the attached SES controller. It is used to sort disks by chassis and slot.
def getSEScontrollerMap():
    results = sortSCSI(sesOnly=True)
    sesControllermap = {}
    for sesPath in results['13']:
        scsiaddr = sesPath.name
        lastExpanderPath = getLastExpanderFullPath(scsiaddr)
        if lastExpanderPath is None:
            print("Unable to create sesControllerMap entry for SCSI address",scsiaddr)
            print(sesPath)
            sesControllermap[sesPath] = scsiaddr
        else:
            sesControllermap[lastExpanderPath] = scsiaddr
    return sesControllermap

def JBODserialNumber2SESControllerMap(serialnumber):
    sesCtrl2ExpMap = {}
    sesControllerMap = getSEScontrollerMap()
    for key in sesControllerMap:
        scsiaddr = sesControllerMap[key]
        serialnumberOfSESController = scsiAddr2SerialNumber(scsiaddr)
        if serialnumberOfSESController == serialnumber:
            sesCtrl2ExpMap[scsiaddr] = key

    if len(sesCtrl2ExpMap) == 0:
        return None
    else:
        return sesCtrl2ExpMap
#  Given the SCSI address of an SES controller, this function returns a dictionary with keys that contain the SCSI address of all the
#  disks controlled by that SES controller. The value is a dictionary that contains at least the SCSI address of the ses Controller.
def sesController2SCSIdisks(scsiaddr):
    if scsiaddr is None:
        return None
    scsiPath = Path('/sys/bus/scsi/drivers/ses').joinpath(scsiaddr)
    if not scsiPath.is_symlink():
        print("Does not appear to be a ses controller.")
        return None
    scsiDevices = sortSCSI()
    scsiDisks = scsiDevices['0']
    if len(scsiDisks) == 0:
        print("No SCSI disks detected on this system")
        return None
    mydisks = {}
    myExpander = getLastExpanderFullPath(scsiaddr)
    for scsiDisk in scsiDisks:
        try:
            scsiDisk.relative_to(myExpander)
            # mydisks.append(scsiDisk.name)
            mydisks[scsiDisk.name] = {'sesControllerSCSI':scsiaddr}
        except ValueError:
            pass
        except Exception as e:
            print("There was an unknown exception when trying to determine SES controller for SCSI disk",scsiDisk.name)
            print(e)
    return mydisks

#  This function takes in the SCSI address of a disk and attempts to return the SES controller SCSI address responsible for it.
#  It optionally takes an object that is the output of getSEScontrollerMap(). Use this parameter if you will call this function
#  repeatedly. It is very expensive if you don't.
def scsiDisk2SEScontroller(scsiaddr,sesControllerMap=None):
    if scsiaddr is None:
        return None
    scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr)
    if scsiPath.is_symlink():
        fullPath = scsiPath.resolve()
    else:
        print("Unable to find the SCSI disk with address:",scsiaddr)
        return None
    if sesControllerMap is None:
        sesControllerMap = getSEScontrollerMap()
    for expander in sesControllerMap:
        try:
            fullPath.relative_to(expander)
            return sesControllerMap[expander]
        except ValueError:
            pass
        except Exception as e:
            print(e)
            print("Unknown exception has occured while trying to lookup the SES controller for disk:",scsiaddr)
            return None

def scsi2JBODchassis(scsiaddr=None):
    if scsiaddr is None:
        print("scsi2JBODchassis: You must provide a SCSI address to this function.")
        return None
    sesPath = Path('/sys/bus/scsi/drivers/ses')
    sdPath = Path('/sys/bus/scsi/drivers/ses')
    if not sesPath.is_dir():
        print("No SES controllers detected on this server.")
        return None
    allSES = [item.name for item in list(sesPath.iterdir())]
    allSD = [item.name for item in list(sdPath.iterdir())]
    if scsiaddr in allSES:
        serialnumber = scsiAddr2SerialNumber(scsiaddr)
        if serialnumber is None:
            print("Unable to get serial number for JBOD")
            return None
        return {'serialnumber':serialnumber}
    elif scsiaddr in allSD:
        sesController = scsiDisk2SEScontroller(scsiaddr)
        if sesController is None:
            print("Unable to determine SES controller for ",scsiaddr)
            return None
        serialnumber = scsiAddr2SerialNumber(sesController)
        if serialnumber is None:
            print("Unable to get serial number for JBOD")
            return None
        return {'serialnumber':serialnumber}
    else:
        print("SCSI device not found with address:",scsiaddr)
        return None
def scsiAddr2Model(scsiaddr=None):
    if scsiaddr is None:
        print("This function requires a SCSI address in the format of a str()")
        return None
    scsiPath = Path('/sys/class/scsi_device')
    devPath = scsiPath.joinpath(scsiaddr).joinpath('device').resolve()
    modelPath = devPath.joinpath('model')
    if modelPath.is_file():
        return modelPath.read_text().strip().lower()
    else:
        print("Model name not found for ",scsiaddr)
        return None

def scsiAddr2Vendor(scsiaddr=None):
    if scsiaddr is None:
        print("This function requires a SCSI address in the format of a str()")
        return None
    scsiPath = Path('/sys/class/scsi_device')
    devPath = scsiPath.joinpath(scsiaddr).joinpath('device').resolve()
    vendorPath = devPath.joinpath('vendor')
    if vendorPath.is_file():
        return vendorPath.read_text().strip()
    else:
        print("Vendor name not found for ",scsiaddr)
        return None

#  This function takes a SCSI address and runs smartctl against the device. You can set the -i -a etc parameter or
#  it will default to -i
def scsiAddr2SMART(scsiaddr=None,switch="i"):

    if '-' in switch:
        switch = switch.lstrip('-')
    if scsiaddr is None:
        print("This function expects the SCSI address of a device that supports SMART statuses.")
        return None
    sgname = scsiAddr2SG(scsiaddr=scsiaddr)
    if sgname is None:
        print("This is not a valid SCSI device.")
        return None
    command = ['smartctl','-'+switch,'/dev/'+sgname,'--json']
    results = errorHandledRunCommand(command=command,timeout=30)
    if results is None or results['returncode'] > 1:
        print("Problem running smartctl on device",scsiaddr)
        return None
    try:
        data = json.loads(results['stdout'])
    except json.JSONDecodeError as j:
        print("The output of this command is not JSON")
        print(j)
        print("see output below:")
        print(results['stdout'])
        return None
    except Exception as e:
        print("unhandled exception inside scsiAddr2SMART")
        print(e)
        return None

def sortEnclosuresByChassisSerial():
    enclByChassisSerial = {}
    sesPaths = sortSCSI(sesOnly=True)
    if sesPaths is None:
        print("No SES controllers detected")
        return None
    try:
        sesSCSI = [item.name for item in sesPaths['13']]
    except Exception:
        print("There was an unknown problem in sortEnclosuresByChassisSerial")
        return None
    for addr in sesSCSI:
        serial = scsiAddr2SerialNumber(addr)
        if serial is None or serial == '':
            serial = str(sesSCSI)+'noserialfound'
        if serial in enclByChassisSerial:
            enclByChassisSerial[serial].append(addr)
        else:
            enclByChassisSerial[serial] = [addr]
    return enclByChassisSerial

#  This funtion wills sort all SCSI disks on the system, or the list passed to it, by jbod chassis serial number
#  and then by SES controller.
def sortSCSIDisks(scsidisks=None,enclByChassisSerial=None,sesControllerMap=None,concurrency=1):
    if enclByChassisSerial is None:
        enclByChassisSerial = sortEnclosuresByChassisSerial()
    if scsidisks is None:
        scsidisks = sortSCSI()['0']
    if sesControllerMap is None:
        sesControllerMap = getSEScontrollerMap()
    if enclByChassisSerial is None or scsidisks is None or sesControllerMap is None:
        print("Failed to sort SCSI disks.")
    # print("enclbychasiss serial",enclByChassisSerial)
    # print('scsidisks',scsidisks)
    # print('ses controller map',sesControllerMap)
    #  define a sub function so that we can use multithreading to make this faster.
    enclResult = {encl:[] for encl in sesControllerMap.values()}
    failedLookupDiskPaths = []

    def findDiskEnclosure(diskPath):
        for expander in sesControllerMap:
            try:
                diskPath.relative_to(expander)
                return sesControllerMap[expander]
            except ValueError:
                pass
            except Exception as e:
                print(e,"inside findDiskEnclosure")
                return None
    #Using multithreading to make this faster.
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_run_loops = {executor.submit(findDiskEnclosure, diskPath=diskPath): diskPath for diskPath in scsidisks}
            for future in concurrent.futures.as_completed(future_run_loops):
                if future.result() is None:
                    failedLookupDiskPaths.append(future_run_loops[future])
                    # print(future_run_loops[future],"result is",future.result())
                else:
                    # print(future_run_loops[future],"result is",future.result())
                    enclResult[future.result()].append(future_run_loops[future])

    masterResult = {}
    # masterResult = {serial:{encl:enclResult[encl] for encl in enclByChassisSerial[serial]} for serial in enclByChassisSerial}
    for serial in enclByChassisSerial:
        masterResult[serial] = {}
        for encl in enclByChassisSerial[serial]:
            masterResult[serial][encl] = enclResult[encl]

    return masterResult

def checkReadPropertyFile(filepath=Path('/')):
    if filepath.is_file():
        data = filepath.read_text().strip()

        if data == '':
            return None
        else:
            if len(data.split()) > 1:
                data = data.split()[0].strip()
            return data
    else:
        print("Unable to locate file.",filepath.as_posix())
        return None

def getMDparent(scsiaddr=None,blockName=None):
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    parents = blockPath.joinpath('holders')
    if parents.is_dir():
        parents = [item.name for item in list(parents.iterdir()) if item.is_symlink()]
    else:
        return None
    if not len(parents) == 0:
        if Path('/sys/block/').joinpath(parents[0]).joinpath('md').is_dir():
            return parents[0]
        else:
            return getMDparent(blockName=parents[0])
    else:
        return None



#----------------------------async functions------------------------------------------------------------------
async def getSMART(sdname,timeout=90):
    print("getSMART has been run with sdname=",sdname," timeout =",timeout)
    # command = ['smartctl', '-a', '--json', '/dev/' + sdname]
    command = 'smartctl -a --json /dev/'+sdname
    # results = errorHandledRunCommand(command=command)
    results = await errorHandledRunCommandaAsync(command=command, timeout=timeout)
    results = results[1]
    if results is None:
        return (sdname,None)
    if results['returncode'] != 0:
        print("There was an error, cannot continue getSMART. See details below\n",
              "stdout:\n" + results['stdout'], "stderr: \n" + results['stderr'])
        print("The return code was ", results['returncode'])
        jdata = {}
    else:
        data = results['stdout']
        jdata = json.loads(data)
    properties = {}
    try:
        properties['protocol'] = jdata['device']['protocol']
    except KeyError:
        properties['protocol'] = ''
    try:
        if jdata['smart_status']['passed']:
            properties['smartstatus'] = 'passed'
        else:
            properties['smartstatus'] = 'failed'
    except KeyError:
        properties['smartstatus'] = ''
    try:
        properties['temperature'] = jdata['temperature']['current']
    except KeyError:
        properties['temperature'] = -1
    try:
        properties['capacity'] = jdata['user_capacity']['bytes']
    except KeyError:
        properties['capacity'] = -1
    try:
        properties['rotationrate'] = jdata['rotation_rate']
    except KeyError:
        properties['rotationrate'] = -1
    if properties['protocol'] == 'ATA':
        ATAproperties = getSMARTata(jdata=jdata)
        properties.update(ATAproperties)
        scsiempty = getSMARTscsi(jdata={'json_format_version':jdata['json_format_version']})
        properties.update(scsiempty)
    elif properties['protocol'] == 'SCSI':
        scsiproperties = getSMARTscsi(jdata=jdata)
        properties.update(scsiproperties)
        ataempty = getSMARTata(jdata={'json_format_version':jdata['json_format_version']})
        properties.update(ataempty)
    # Items below this are not actually provided by smartctl -a --json but are included in the properties dictionary for later filling from other sources.
    try:
        properties['health'] = ''
    except KeyError:
        properties['health'] = ''
    try:
        properties['indicatorled'] = False
    except KeyError:
        properties['indicatorled'] = False
    # self.smartPopulated = True
    # self.attributes.update(properties)
    print("Leaving getsmart.")
    # return (sdname,properties)
    return (sdname,'getsmartreturnvalue')
def getSMARTata(jdata={}):
    try:
        ATAattributes = {item['name']: item['value'] for item in jdata['ata_smart_attributes']['table']}
    except KeyError:
        ATAattributes = {}
    try:
        ATAattributes['firmware'] = jdata['firmware_version']
    except KeyError:
        pass
    try:
        ATAattributes['model'] = jdata['model_name']
    except KeyError:
        pass
    try:
        ATAattributes['vendor'] = jdata['model_family']
    except KeyError:
        pass
    return ATAattributes

def getSMARTscsi(jdata={}):
    try:
        json_format_version = jdata['json_format_version']
        if json_format_version == [1, 0]:
            return getSMARTscsi10(jdata=jdata)
        elif json_format_version == [2, 0]:
            print("I don't know how to parse this json yet. Tell Hancock")
        else:
            return getSMARTscsi10(jdata=jdata)
    except KeyError:
        print("Unable to determine json format version. assuming 1,0")
    return getSMARTscsi10(jdata=jdata)

def getSMARTscsi10(jdata):
    properties = {}
    try:
        properties['vendor'] = jdata['vendor']
    except KeyError:
        print("Key error on vendor scsi")
        properties['vendor'] = ''
    try:
        properties['model'] = jdata['product']
    except KeyError:
        print("Key error on model scsi")
        properties['model'] = ''
    try:
        properties['firmware'] = jdata['revision']
    except KeyError:
        properties['firmware'] = ''
    try:
        properties['growndefects'] = jdata['scsi_grown_defect_list']
    except KeyError:
        properties['growndefects'] = -1
    try:
        properties['scsi_error_counter_log'] = jdata['scsi_error_counter_log']
    except KeyError:
        properties['scsi_error_counter_log'] = None
    try:
        properties['readerrorcorrectedtotal'] = jdata['scsi_error_counter_log']['read']['total_errors_corrected']
    except KeyError:
        properties['readerrorcorrectedtotal'] = 0
    try:
        properties['readerroruncorrectedtotal'] = jdata['scsi_error_counter_log']['read'][
            'total_uncorrected_errors']
    except KeyError:
        properties['readerroruncorrectedtotal'] = 0
    try:
        properties['readerrorcorrectedbyreadwrite'] = jdata['scsi_error_counter_log']['read'][
            'errors_corrected_by_rereads_rewrites']
    except KeyError:
        properties['readerrorcorrectedbyreadwrite'] = 0
    try:
        properties['readerrorcorrectedeccfast'] = jdata['scsi_error_counter_log']['read'][
            'errors_corrected_by_eccfast']
    except KeyError:
        properties['readerrorcorrectedeccfast'] = 0
    try:
        properties['readerrorcorrectedeccdelayed'] = jdata['scsi_error_counter_log']['read'][
            'errors_corrected_by_eccdelayed']
    except KeyError:
        properties['readerrorcorrectedeccdelayed'] = 0

    try:
        properties['verifyerrorcorrectedtotal'] = jdata['scsi_error_counter_log']['verify'][
            'total_errors_corrected']
    except KeyError:
        properties['verifyerrorcorrectedtotal'] = 0
    try:
        properties['verifyerroruncorrectedtotal'] = jdata['scsi_error_counter_log']['verify'][
            'total_uncorrected_errors']
    except KeyError:
        properties['verifyerroruncorrectedtotal'] = 0
    try:
        properties['verifyerrorcorrectedbyreadwrite'] = jdata['scsi_error_counter_log']['verify'][
            'errors_corrected_by_rereads_rewrites']
    except KeyError:
        properties['verifyerrorcorrectedbyreadwrite'] = 0
    try:
        properties['verifyerrorcorrectedeccfast'] = jdata['scsi_error_counter_log']['verify'][
            'errors_corrected_by_eccfast']
    except KeyError:
        properties['verifyerrorcorrectedeccfast'] = 0
    try:
        properties['verifyerrorcorrectedeccdelayed'] = jdata['scsi_error_counter_log']['verify'][
            'errors_corrected_by_eccdelayed']
    except KeyError:
        properties['verifyerrorcorrectedeccdelayed'] = 0

    try:
        properties['writeerrorcorrectedtotal'] = jdata['scsi_error_counter_log']['write']['total_errors_corrected']
    except KeyError:
        properties['writeerrorcorrectedtotal'] = 0
    try:
        properties['writeerroruncorrectedtotal'] = jdata['scsi_error_counter_log']['write'][
            'total_uncorrected_errors']
    except KeyError:
        properties['writeerroruncorrectedtotal'] = 0
    try:
        properties['writeerrorcorrectedbyreadwrite'] = jdata['scsi_error_counter_log']['write'][
            'errors_corrected_by_rereads_rewrites']
    except KeyError:
        properties['writeerrorcorrectedbyreadwrite'] = 0
    try:
        properties['writeerrorcorrectedeccfast'] = jdata['scsi_error_counter_log']['write'][
            'errors_corrected_by_eccfast']
    except KeyError:
        properties['writeerrorcorrectedeccfast'] = 0
    try:
        properties['writeerrorcorrectedeccdelayed'] = jdata['scsi_error_counter_log']['write'][
            'errors_corrected_by_eccdelayed']
    except KeyError:
        properties['writeerrorcorrectedeccdelayed'] = 0

    return properties

def multiExecute(functionName, kwargs=[{}]):#This function takes a function name, and a list of kwarg dictionaries
    results = {}          #one for each copy you want to run in parallel.
                                            #all functions should return a returnCode, not None.
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_run_loops = {executor.submit(functionName,**argset): argset for argset in kwargs}
        for future in concurrent.futures.as_completed(future_run_loops):
            if future.result() is None:
                print("There was an error on running ",future_run_loops[future])
            submissionID = ''
            for key in future_run_loops[future]:
                submissionID = submissionID+str(key)+':'+str(future_run_loops[future][key])+' '
            results[submissionID] = future.result()
    return results

def multiExecuteAsync(funcName,kwargs=[{}]): #take an arbitrary coroutine and execute it over a set of key word arguments
    if not asyncio.iscoroutinefunction(funcName):
        print("This is not an asyncio coroutine function. It cannot be used with this multiexecute function.")
        return None
    loop = asyncio.get_event_loop()
    tasks = [funcName(**kwarg) for kwarg in kwargs]
    results = loop.run_until_complete(asyncio.gather(*tasks,return_exceptions=True))
    output = {}
    for i in range(len(results)):
        submissionID = ''
        for key in kwargs[i]:
            submissionID = submissionID+str(key)+':'+str(kwargs[i][key])+' '
            output[submissionID] = results[i]
    return output

def multiExecuteExternal(commandStrings,timeout=90):
    pass #This function takes a bash command line function and a set of arguments and a set of keyword:value arguments. It assembles the command and passes to errorHandledRunCommandasync
    commands = [command for command in commandStrings]
    loop = asyncio.get_event_loop()
    tasks = [errorHandledRunCommandaAsync(command=command, timeout=timeout) for command in commands]
    results = loop.run_until_complete(asyncio.gather(*tasks,return_exceptions=True))
    # results = asyncio.wait_for(asyncio.gather(*tasks),timeout=timeout)
    results = {item[0]:item[1] for item in results}
    return results

def errorHandledRunCommand(command=None,timeout=29,autoretry=True):
    myenv = environ.copy()
    bitmaskflagreturn = False
    if command is None:
        print("This function requires a command. it can be a string or a list format.")
        return None
    elif type(command) == str:
        command = command.split()
    if command[0].lower() in ['smartctl']: #Some command line programs return have a return code formatted as bitmask.
        bitmaskflagreturn = True
    tempCommandTracker = Path('/tmp').joinpath('externalcommandtracker.log')
    with tempCommandTracker.open(mode='a') as f:
        if 'sg_ses' in command:
            f.write(str(command)+"\n")
    try:
        start = perf_counter()
        proc = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,env=myenv)
        time_spent = perf_counter() - start
        #print("ran this command in a normal subprocess shell.",command)
    except subprocess.TimeoutExpired:
        print("Time expired when trying to run command",command)
        if autoretry:
            tryAgain = errorHandledRunCommand(command=command,timeout=timeout,autoretry=False)
            if tryAgain is None:
                print(command,"Failed to run twice.")
                traceback.print_stack()
            return tryAgain
        else:
            return None
    except Exception as e:
        print("An unknown exception occured when trying to run command",command)
        print(e)
        return None
    output = proc.stdout.decode()
    errors = proc.stderr.decode()
    if proc.returncode != 0:
        if bitmaskflagreturn:#This is decoding the return code. We only report a bad return if bit 0 or 1 are set indicating a problem with the command line execution of the device communication.
            bitflags = [bool(int(num)) for num in bin(int(proc.returncode)).lstrip('0b')]
            if bitflags[-1] or bitflags[-2]:
                proc.returncode = -1
                print(command, "Returned a non-zero return code")
                print(proc.stderr.decode())
            else:
                proc.returncode = 0
    return {'returncode':proc.returncode,'stdout':output,'stderr':errors,'timespent':time_spent}


async def errorHandledRunCommandaAsync(command=None, timeout=90):
    myenv = environ.copy()
    bitmaskflagreturn = False
    if command is None:
        print("This function requires a command. It must be string.")
        return (command,None)
    elif type(command) != str:
        print("This function requires a string command.")
        return (command,None)

    if command[0].lower() in ['smartctl']: #Some command line programs return have a return code formatted as bitmask.
        bitmaskflagreturn = True
    try:
        proc = await asyncio.wait_for(asyncio.create_subprocess_shell(command,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,env=myenv),timeout=timeout)
        print("ran this command in async subprocess shell.",command)
    except subprocess.TimeoutExpired:
        print("Time expired when trying to run command",command)
        return (command,None)
    except Exception as e:
        print("An unknown exception occured when trying to run command",command)
        print(e)
        return (command,None)
    stdout, stderr = await proc.communicate()
    output = stdout.decode()
    errors = stderr.decode()
    returnCode = proc.returncode
    if returnCode != 0:
        if bitmaskflagreturn:#This is decoding the return code. We only report a bad return if bit 0 or 1 are set indicating a problem with the command line execution of the device communication.
            bitflags = [bool(int(num)) for num in bin(int(returnCode)).lstrip('0b')]
            if bitflags[-1] or bitflags[-2]:
                returnCode = -1
                print(command, "Returned a non-zero return code")
                print(returnCode)
            else:
                returnCode = 0
    return (command,{'returncode':returnCode,'stdout':output,'stderr':errors})

from pprint import pprint
def generateSAS2SerialMap(chassisSerial,sortBySerial=False,sortedDisks=None):
    if sortedDisks is None:
        sortedDisks = sortSCSIDisks()
    if chassisSerial not in sortedDisks:
        print("There was an error trying to generate SAS2Serial map. The JBOD chassis serial number",chassisSerial,'does not exist.')
        exit(1)

    kwargs = []
    for encl in sortedDisks[chassisSerial]:
        for fullpath in sortedDisks[chassisSerial][encl]:
            kwargs.append({'scsiaddr':fullpath.name})
    # kwargs = [{'scsiaddr':item}for item in scsidevices]
    scsisasmap = multiExecute(scsiAddr2SASaddr,kwargs=kwargs)

    scsiserialmap = multiExecute(scsiAddr2SerialNumber,kwargs=kwargs)
    sasserialmap = {}
    for key in scsisasmap:
        if scsisasmap[key] is not None:
            try:
                sasserialmap[scsisasmap[key][1]] = scsiserialmap[key]
            except KeyError as k:
                print(k)
    if sortBySerial:
        output = {sasserialmap[key]:key for key in sasserialmap}
    else:
        output = sasserialmap
    return output

def generateSAS2SerialMapAsync(chassisSerial, sortBySerial=False, sortedDisks=None):
    if sortedDisks is None:
        sortedDisks = sortSCSIDisks()
    if chassisSerial not in sortedDisks:
        print("There was an error trying to generate SAS2Serial map. The JBOD chassis serial number", chassisSerial,
              'does not exist.')
        exit(1)

    kwargs = []
    for encl in sortedDisks[chassisSerial]:
        for fullpath in sortedDisks[chassisSerial][encl]:
            kwargs.append({'scsiaddr': fullpath.name})
    scsisasmap = multiExecute(scsiAddr2SASaddr, kwargs=kwargs)
    # In some instances SAS addresses are not unique across all JBODs attached to server. We handle that case here.

    scsiserialmap = multiExecuteAsync(scsiAddr2SerialNumberAsync, kwargs=kwargs)
    sasserialmap = {}
    for key in scsisasmap:
        if scsisasmap[key] is not None:
            try:
                sasserialmap[scsisasmap[key]] = scsiserialmap[key][1]
            except KeyError as k:
                print(k)
    if sortBySerial:
        output = {sasserialmap[key]: key for key in sasserialmap}
    else:
        output = sasserialmap
    return output

def getAllTopParents(blockName=None,scsiaddr=None,currparents=[]):
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    parents = blockPath.joinpath('holders')
    if parents.is_dir():
        parents = [item.name for item in list(parents.iterdir()) if item.is_symlink()]
    else:
        return None
    if len(parents) == 0:
        print("i have no parents so returning",blockName,"\n")
        return blockName
    else:
        mytops = currparents
        print("mytops is currently",mytops,"\n")
        for parent in parents:
            print("recursively calling on my parents",parent,"\n")
            result = getAllTopParents(blockName=parent,currparents=mytops)
            if result is not None:
                print("The result is not none it is ",result,"\n")
                if type(result) ==  str:
                    mytops.append(result)
                elif type(result) == list:
                    mytops.extend(result)

            else:
                print("The result is none.")
                print("returning contents of mytops",mytops,'\n')
                return mytops
        return list(set(mytops))

def flushmpath(blockDevName,info):
    # blockDevName = name of a block device on the system
    # info = instance of storage_info object
    target = None
    validDiskDevices = ['logicaldisks', 'multipaths', 'raidpartitions', 'harddrives']
    try:
        targettype = info.name2type[blockDevName]
    except Exception as e:
        print(e)
        targettype = None
    if targettype not in validDiskDevices:
        print(blockDevName," of type",targettype,"cannot have a corresponding multipath device. GoodBye")
        return None
    if targettype == 'multipaths':
        print("targettype is multipaths")
        if blockDevName in info.multipaths:
            target = info.multipaths[blockDevName]['name']
        else:
            target = blockDevName
    elif targettype == 'logicaldisks':
        print("targettype is logicaldisks")
        target = getmpathparent(info=info,blockName=blockDevName,friendlyname=True)
    elif targettype == 'harddrives':
        print("targettype is harddrives")
        xdata = info.exportDictionary()
        target = xdata['harddrives'][blockDevName]['children'][0]
        target = getmpathparent(info=info,blockName=target,friendlyname=True)
    elif targettype == 'raidpartitions':
        print("targettype is raidpartitions")
        serialnumber = blockDevName2SerialNumber(blockName=blockDevName)
        xdata = info.exportDictionary()
        target = xdata['harddrives'][serialnumber]['children'][0]
        target = getmpathparent(info=info,blockName=target,friendlyname=True)
    if target is None:
        print(blockDevName," has no multipath parent.")
    if target in info.name2type and info.name2type[target] == 'multipaths':
        command = ['multipath','-f',target]
        #print(command)
        #result = {'returncode':0,'stdout':'its fine','stderr':'None'}
        result = errorHandledRunCommand(command=command)
        if result is None or result['returncode'] != 0:
            print("There was a problem flushing",target,"which is the multipath parent of ",blockDevName)
            if result is not None:
                print(result)
            return None
        else:
            print("The multipath map for",target," has been flushed.")
            return 1
    else:
        print("utter failure")
        print(target,info.name2type[target])

def getmpathparent(scsiaddr=None,blockName=None,friendlyname=False,info=None):
    #  info is a storage_info class instance/
    if info is None:
        return getmpathparentStandalone(scsiaddr=scsiaddr,blockName=blockName,friendlyname=friendlyname)
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    parents = blockPath.joinpath('holders')
    if parents.is_dir():
        parents = [item.name for item in list(parents.iterdir()) if item.is_symlink()]
    else:
        return None
    if not len(parents) == 0:
        if info.name2type[parents[0]] == 'multipaths':
            if friendlyname and parents[0] in info.multipaths:
                return info.multipaths[parents[0]].attributes['name']
            else:
                return parents[0]
        else:
            return getmpathparent(blockName=parents[0],info=info)
    else:
        return None

def getmpathparentStandalone(scsiaddr=None,blockName=None,friendlyname=False):
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    if blockName[:2] == 'dm':
        dmDev = Path('/sys').joinpath('block').joinpath(blockName)
        fields = dmDev.joinpath('dm').joinpath('uuid').read_text().strip().split('-')
        if 'mpath' in fields[0]:
            if friendlyname:
                return dmDev.joinpath('dm').joinpath('name').read_text().strip()
            else:
                return blockName
    parents = blockPath.joinpath('holders')
    if parents.is_dir():
        parents = [item.name for item in list(parents.iterdir()) if item.is_symlink()]
    else:
        return None
    if not len(parents) == 0:
        return getmpathparentStandalone(blockName=parents[0],friendlyname=friendlyname)
    else:
        return None


def getraidpartition(scsiaddr=None,blockName=None,friendlyname=False,info=None):
    #  info is a storage_info class instance/
    if info is None:
        return getraidpartitionStandalone(scsiaddr=scsiaddr,blockName=blockName,friendlyname=friendlyname)
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    parents = blockPath.joinpath('holders')
    if parents.is_dir():
        parents = [item.name for item in list(parents.iterdir()) if item.is_symlink()]
    else:
        return None
    if not len(parents) == 0:
        if info.name2type[parents[0]] == 'raidpartitions':
            if friendlyname and parents[0] in info.dm_partitions:
                return info.dm_partitions[parents[0]].attributes['name']
            else:
                return parents[0]
        else:
            return getraidpartition(blockName=parents[0],info=info,friendlyname=friendlyname)
    else:
        return None

def getraidpartitionStandalone(scsiaddr=None,blockName=None,friendlyname=False,mdparent=''):
    if mdparent == '':
        mdparent = getMDparent(blockName=blockName)
        if mdparent is None:
            return None
    elif mdparent is None:
        return None
    #  info is a storage_info class instance/
    if scsiaddr is not None:
        scsiPath = Path('/sys/bus/scsi/devices').joinpath(scsiaddr).resolve()
        if scsiPath.joinpath('block').is_dir():
            blockPath = list(scsiPath.joinpath('block').iterdir())[0]
        else:
            print("Not a block device corresponding to SCSI address",scsiaddr)
            return None
    elif blockName is not None:
        blockPath = Path('/sys/block').joinpath(blockName)
        if not blockPath.is_dir():
            print("Block device ",blockName,"not found.")
            return None
    else:
        print("You must pass in either the scsi address or the block name of the device you want children for.")
        return None
    parents = blockPath.joinpath('holders')
    if parents.is_dir():
        parents = [item.name for item in list(parents.iterdir()) if item.is_symlink()]
    else:
        return None
    if not len(parents) == 0:
        if parents[0] == mdparent:
            devpath = Path('/sys/block').joinpath(blockName)
            if friendlyname and devpath.joinpath('dm').is_dir():
                return devpath.joinpath('dm').joinpath('name').read_text().strip()
            else:
                return blockName
        else:
            return getraidpartitionStandalone(blockName=parents[0],friendlyname=friendlyname,mdparent=mdparent)
    else:
        return None

