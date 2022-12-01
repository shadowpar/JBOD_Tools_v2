import concurrent.futures
import traceback
from pathlib import Path
from re import search

from hancockStorageMonitor.common.staticdatastorage import NEWJBODMODELS
from hancockStorageMonitor.localgatherers.scsiOperations import scsiAddr2SG, scsiAddr2Model, sg2SCSIaddr, \
    errorHandledRunCommand, generateSAS2SerialMap, scsiAddr2BlockDevName
from hancockStorageMonitor.localgatherers.scsiOperations import sortSCSI, blockDevName2SerialNumber


#  This function will return a dictionary of the form {indexNumber:{'serialnumber':serialNumber,'index':index,'slot':slot}}
#  This function can only be used on newer model JBODs. The model number of such JBODs is stored in the list below.
def newJbodFindSlotNumbers(scsiaddr=None,sgname=None,sortBySerial=False):
    newModels = NEWJBODMODELS
    if scsiaddr is not None:
        scsiSESPath = Path('/sys/bus/scsi/drivers/ses').joinpath(scsiaddr)
        if not scsiSESPath.is_symlink():
            return None
        sgname = scsiAddr2SG(scsiaddr)
    if sgname is None:
        print("Unable to find scsi generic name for SES controller with SCSI address",scsiaddr)
        return None
    if scsiaddr is None:
        scsiaddr = sg2SCSIaddr(sgname)
    sgPath = Path('/dev').joinpath(sgname)
    if not sgPath.is_char_device():
        print("This does not appear to be a valid SES controller SCSI generic name.")
        return None
    if scsiAddr2Model(scsiaddr).lower() not in newModels:
        print("This function can only be used on newer model JBODs. Calling the older function instead.")
        print("Your model is ",scsiAddr2Model(scsiaddr).lower())
        print("Known new models are ",newModels)
        #  If the preferred function cannot be used, call the older one instead.
        return oldJbodFindSlotNumbers(scsiaddr=scsiaddr,sortBySerial=True)
    disksByIndex = {}
    command = ['sg_ses','-p','ed','/dev/'+sgname]
    results = errorHandledRunCommand(command=command,timeout=60)
    if results is None or results['returncode'] != 0:
        print("There was an error inside newJbodFindSlotNumbers")
        return None
    output = results['stdout'].splitlines()
    startSection = False
    for line in output:
        if  not startSection and 'element type:' in line.lower() and 'array device slot' in line.lower():
            startSection = True
            continue
        elif startSection and 'element type:' in line.lower():
            break
        elif startSection and 'descriptor: slot' in line.lower():
            parts = line.split()
            index = parts[1]
            innerParts = parts[4].split(',')
            slot = innerParts[0].lstrip('0')
            if slot == '':
                slot = '0'
            driveSerial = innerParts[1]
            if driveSerial != '':
                disksByIndex[index] = {'index':index,'slot':slot,'serialnumber':driveSerial}
    if len(disksByIndex) == 0:
        print("no disks detected in jbod")
        return None
    else:
        if sortBySerial:
            disksBySerial = {disksByIndex[index]['serialnumber']:{'index':disksByIndex[index]['index'],'slot':disksByIndex[index]['slot']} for index in disksByIndex}
            return disksBySerial
        return disksByIndex


#----------TO DO----------Optimize oldJbodFindSlotNumbers by using serial2SASMap------------------------
def oldJbodFindSlotNumbers(scsiaddr=None, sgname=None, sortBySerial=False, sas2SerialMap=None):
    # print("Entering old JbodFindslotnumbers")
    if scsiaddr is not None:
        scsiSESPath = Path('/sys/bus/scsi/drivers/ses').joinpath(scsiaddr)
        if not scsiSESPath.is_symlink():
            print("The SCSI device with address",scsiaddr,"does not look like an SES controller.")
            return None
        sgname = scsiAddr2SG(scsiaddr)
    if sgname is None:
        print("Unable to find scsi generic name for SES controller with SCSI address",scsiaddr)
    sgPath = Path('/dev').joinpath(sgname)
    if not sgPath.is_char_device():
        print("This does not appear to be a valid SES controller SCSI generic name.")
    chassisSerial = blockDevName2SerialNumber(blockName=sgname)
    if sas2SerialMap is None:
        # print("trying to generateSAS2Serial")
        sas2SerialMap = generateSAS2SerialMap(chassisSerial=chassisSerial)
    # print("about to getGenericJBODinfo")
    sas2indexmap = getGenericJBODInfo(sgname=sgname,sortBySAS=False)
    #above is sorted by index because of sortBySAS=False
    disksByIndex = {}
    for index in sas2indexmap:
        disksByIndex[str(index)] = {'index':str(index)}
        disksByIndex[str(index)]['slot'] = str(sas2indexmap[index]['slot'])
        disksByIndex[str(index)]['sasaddress'] = str(sas2indexmap[index]['sasaddress'])
        try:
            disksByIndex[str(index)]['serialnumber'] = str(sas2SerialMap[sas2indexmap[index]['sasaddress']])
        except KeyError as k:
            print(k)
            disksByIndex[str(index)]['serialnumber'] = None

    if sortBySerial:
            disksBySerial = {disksByIndex[index]['serialnumber']:{'index':disksByIndex[index]['index'],'slot':disksByIndex[index]['slot']} for index in disksByIndex if 'serialnumber' in disksByIndex[index]}
            # print("Leaving old JbodFindSlotNumbers")
            return disksBySerial
    # print("leaving old JbodFindslotnumbers")
    return disksByIndex

def getJBODlogicalID(scsiaddr=None,sgname=None):
    if sgname is None:
        if scsiaddr is None:
            print("getJBODLogicalID: You must provide either the sgname or SCSI address of an SES  controller to use this function.")
            traceback.print_stack()
            return None
        else:
            sgname = scsiAddr2SG(scsiaddr=scsiaddr)
    else:
        scsiaddr = sg2SCSIaddr(sgname=sgname)
        if scsiaddr is None:
            print("There was an error trying to get the scsiaddr for ",sgname)
            return None
    if sgname is None or not Path('/sys/class/scsi_generic').joinpath(sgname).joinpath('device').joinpath(
        'type').read_text().strip() == '13':
        print("The sgname or SCSI address provided does not appear to be an SES controller.", scsiaddr, sgname)
        return
    enclosurePathIDfile = Path('/sys/class/scsi_generic').joinpath(sgname).joinpath('device').joinpath('enclosure').joinpath(scsiaddr).joinpath('id')
    if  enclosurePathIDfile.is_file():
        logicalid = enclosurePathIDfile.read_text().strip().lstrip('0x')
        return logicalid
    else:
        command = ['sg_ses','-p','ed','/dev/'+sgname]
        result = errorHandledRunCommand(command=command,timeout=90)
        if result is None or result['returncode'] > 0:
            print("Unable to find logicalID for ",scsiaddr,sgname)
            return None
        lines = result['stdout'].splitlines()[0:5]
        logicalid = [item.split()[-1].strip().lstrip('0x') for item in lines if 'logical identifier' in item.lower()]
        if len(logicalid) == 1:
            return logicalid[0]
        else:
            print("Failed to find logical id using sg_ses command on ",sgname)
            return None

def getGenericJBODInfo(sgname=None,scsiaddr=None,sortBySAS=True): #if sortBySAS is true the output is keys with SAS addresses if not it is keyed with indexes.
    if sgname is None:
        if scsiaddr is None:
            print("oldJbodGetSAS2Index: You must provide either the sgname or SCSI address of an SES  controller to use this function.")
            return None
        else:
            sgname = scsiAddr2SG(scsiaddr=scsiaddr)
    if sgname is None or not Path('/sys/class/scsi_generic').joinpath(sgname).joinpath('device').joinpath('type').read_text().strip() == '13':
        print("The sgname or SCSI address provided does not appear to be an SES controller.",scsiaddr,sgname)
        return None
    command = ['sg_ses','-p','aes','/dev/'+sgname]
    results = errorHandledRunCommand(command=command,timeout=90)
    if results is None or results['returncode'] > 0:
        print("Problem inside oldJbodFindSlotNumbers")
        return None
    output = results['stdout'].splitlines()
    output = [line.lower() for line in output]
    diskInfos = {}
    insideslotsection = False
    # insideslot = False
    index = slot = sasaddr = None
    for line in output:
        if not insideslotsection and 'element type' in line and 'slot' in line:
            insideslotsection = True
            continue
        elif insideslotsection and 'element type' in line:
            insideslotsection = False
            if index is not None:
                diskInfos[index] = {'slot':slot,'sasaddress':sasaddr}
            break
        if not insideslotsection:
            continue
        if 'element index' in line:
            if index is not None:
                diskInfos[index] = {'slot':slot,'sasaddress':sasaddr}
                index=slot=sasaddr=None
            index = line.split()[2].strip()
        elif 'device slot' in line:
            slot = line.split()[-1].strip()
        elif 'attached' not in line and 'sas address' in line:
            sasaddr = line.split()[-1].lstrip('0x').strip()
    if sortBySAS:
        diskinfo = {diskInfos[key]['sasaddress']:{'index':int(key),'slot':int(diskInfos[key]['slot'])} for key in diskInfos if len(diskInfos[key]['sasaddress']) != 0}
    else:
        diskinfo = {int(key):{'slot':int(diskInfos[key]['slot']),'sasaddress':diskInfos[key]['sasaddress']} for key in diskInfos if len(diskInfos[key]['sasaddress']) != 0}
        diskinfo = {key:diskinfo[key] for key in sorted(diskinfo)}
    return diskinfo

#  info = storage_info() class instance
#  blockDevName= name of a block device on the system found in /dev/
#
def blinkMod(*, blockDevName=None, index=None, enclsg=None, chassisSerial=None, info=None, status='on'):
    args = {'blockDevName':blockDevName,'index':index,'enclsg':enclsg,'chassisSerial':chassisSerial,'info':info, 'status':status}
    passedArgs = tuple([key for key in args if args[key] is not None])
    statflip = {'on': '--set', 'off':'--clear'}
    if status not in statflip:
        print("Please ensure parameter status is either 'on' or 'off'.")
        return
    print({item:args[item] for item in passedArgs})
    ready = False

    def bdninfo():
        # Write function to modify light status given blockDevName and info=storage_info() object
        print("I have the needed items to blink the light using blockDevName and info")
        try:
            xdata = info.exportDictionary(write=False)
            print("stop 1")
            serialnumber = blockDevName2SerialNumber(blockName=blockDevName)
            print("stop 2")
            ind = xdata['harddrives'][serialnumber]['index']
            ind = int(ind)
            print("stop 3")
            cserial = xdata['harddrives'][serialnumber]['chassisSerial']
            print("stop 4")
            encl = list(info.disksByChassisEnclosure[cserial].keys())[0]
            print("stop 5")
            encl = scsiAddr2SG(encl)
            if encl is None:
                raise Exception("Unable to determine which chassis disk belongs too.")
            return (True,str(ind),str(encl))
        except Exception as e:
            print(e)
            print("Please ensure parameter blockDevName is a string object that represents the name of a block device on the system.")
            print("Please ensure the info parameter is an instance of storage_info() class.")
            return (False,None,None)

    def indencl():
        # Write function to modify light status given index and enclosure SG name
        print("I have the needed items to blink the light using index and enclsg")
        try:
            ind = int(index)
            if 'sg' not in enclsg:
                raise Exception(str(enclsg)+" does not appear to be a valid enclosure SG name.")
            return (True, str(ind), str(enclsg))
        except Exception as e:
            print(e)
            print("Please ensure that parameter index is an int or a string that can be cast as an int.")
            print("please ensure that encl is a string like 'sg1' that refers to a SES controller on the relevant disk chassis.")
            return (False, None, None)

    def indinfocserial():
        # Write function to modify light status given index, info=storage_info() object, and chassisSerialNumber
        print("I have the needed items to blink the light using index, info, and chassisSerial")
        try:
            encl = list(info.disksByChassisEnclosure[chassisSerial].keys())[0]
            encl = scsiAddr2SG(encl)
            return (True, str(index), str(encl))
        except Exception as e:
            print(e)
            print("Please ensure that parameter index is an int or a string that can be cast as an int.")
            print("Please ensure the info parameter is an instance of storage_info() class.")
            print("Please ensure the chassisSerial parameter is a string object that represents the serial number of the relevant disk chassis.")
            return (False, None, None)

    #  Check for a valid combination of possible parameters.
    validCombos = {('blockDevName','info'):bdninfo,('index','enclsg'):indencl,('index','info','chassisSerial'):indinfocserial}
    validargdetected = False
    for key in validCombos:
        if set(key).issubset(set(passedArgs)):
            validargdetected = True
            results = validCombos[key]()
            ready = results[0]
            index = results[1]
            enclsg = results[2]
            break
    if not validargdetected:
        print("No valid combination of parameters detected. The following are valid combinations of parameters")
        print(validCombos.keys())
    if ready:
        print("index=",index,"enclsg=",enclsg)

        try:
            command = ['sg_ses','--index='+index,statflip[status],'Ident','/dev/'+enclsg]
            result = errorHandledRunCommand(command=command)
            if result is None or result['returncode'] != 0:
                print("There was an issue trying to turn on the locator light for index",index,"of enclosure /dev/"+enclsg)
            else:
                print("The locator light has been set to ",status)
            command = ['sg_ses','--index='+index,statflip[status],'Fault','/dev/'+enclsg]
            result = errorHandledRunCommand(command=command)
            if result is None or result['returncode'] != 0:
                print("There was an issue trying to modify the Fault light for index",index,"of enclosure /dev/"+enclsg)
            else:
                print("The fault light has been set to ",status)
        except Exception as e:
            print(e)
            print("\nThere was some unknown issue with modifying the lights.")
            return
    else:
        print("Unable to change the light status.")







