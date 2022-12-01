from hancockStorageMonitor.localgatherers.scsiOperations import scsiAddr2Model, scsiAddr2Vendor, sortEnclosuresByChassisSerial, sortSCSIDisks, errorHandledRunCommand, scsiAddr2BlockDevName
from hancockStorageMonitor.localgatherers.scsiOperations import blockDevName2SerialNumber, blockDevName2SASaddr, scsiDisk2SEScontroller, blockDevName2SCSIaddr, scsiAddr2SG, getraidpartition, getmpathparent
from hancockStorageMonitor.localgatherers.sesOperations import getJBODlogicalID, newJbodFindSlotNumbers, oldJbodFindSlotNumbers
from pprint import pformat
import json, asyncio

class storage_device(object):
    def __init__(self,uniqueID):
        self.attributes = {'uniqueID':uniqueID}
    def __repr__(self):
        result = str(type(self))+"\n"+pformat(self.attributes)
        return result
    def exportDictionary(self,properties={}):
        data = {}
        for item in self.attributes:
            try:
                json.dumps(self.attributes[item])
                #data[self.attributes['uniqueID']][item] = self.attributes[item]
                data[item] = self.attributes[item]
            except(TypeError,OverflowError):
                data[item] = str(self.attributes[item])
        data.update(properties)
        return data

class storage_jbod(storage_device):
    def __init__(self,uniqueID,sesControllers=None,disksByEnclosure=None):
        super().__init__(uniqueID=uniqueID)
        self.serialnumber = uniqueID
        if sesControllers is None:
            sesControllers = sortEnclosuresByChassisSerial()[self.serialnumber]
        self.sesControllers = sesControllers
        if disksByEnclosure is None:
            disksByEnclosure = sortSCSIDisks()[self.serialnumber]
        self.disksByEnclosure = disksByEnclosure
        self.attributes['serialnumber'] = self.serialnumber
        self.model = self.attributes['model'] = scsiAddr2Model(self.sesControllers[0])
        self.vendor = self.attributes['vendor'] = scsiAddr2Vendor(self.sesControllers[0])
        self.logicalid = self.attributes['logicalid'] = getJBODlogicalID(scsiaddr=sesControllers[0])
        self.datacenter = self.attributes['datacenter'] = 'error'
        self.rack = self.attributes['rack'] = 'error'
        self.slot = self.attributes['slot'] = -1
        self.health = self.attributes['health'] = 'error'
        self.numslots = self.attributes['numslots'] = self.getNumberSlots()
        self.managementmaca = self.attributes['managementmaca'] = 'error'
        self.managementipa = self.attributes['managementipa'] = 'error'
        self.managementstatusa = self.attributes['managementstatusa'] = 'error'
        self.managementmacb = self.attributes['managementmacb'] = 'error'
        self.managementipb = self.attributes['managementipb'] = 'error'
        self.managementstatusb = self.attributes['managementstatusb'] = 'error'
        self.modified = self.attributes['modified'] = 'error'
        self.sesControllerObjects = {}
        for item in disksByEnclosure:
            self.sesControllerObjects[item] = storage_ses(uniqueID=item)
        self.serial2slotMap = {}
        self.serial2LightsMap = {'fault':False,'ident':False}

    def getNumberSlots(self):

        numdisks = 0
        for encl in self.disksByEnclosure:
            if len(self.disksByEnclosure[encl]) > numdisks:
                numdisks = len(self.disksByEnclosure[encl])
        for encl in self.disksByEnclosure:
            enclsg = scsiAddr2SG(encl)
            slotCount = 0
            result = errorHandledRunCommand(['sg_ses','-p','ed','/dev/'+enclsg],timeout=90)
            inSection = False
            if result is not None and result['returncode'] == 0:
                for line in result['stdout'].splitlines(keepends=False):
                    theLine = line.lower()
                    if not inSection:
                        if 'type' in theLine and 'slot' in theLine:
                            inSection = True
                            continue
                    elif inSection:
                        if 'type' in theLine:
                            break
                        elif 'descriptor' in theLine and 'slot' in theLine:
                            slotCount = slotCount +1
            else:
                print("The result was none.")
                continue
            if slotCount > numdisks:
                return slotCount
        return numdisks




class storage_jbod_new(storage_jbod):
    def __init__(self,uniqueID,sesControllers=None):
        super().__init__(uniqueID=uniqueID,sesControllers=sesControllers)
        try:
            self.serial2slotMap = newJbodFindSlotNumbers(scsiaddr=self.sesControllers[0],sortBySerial=True)
            if self.serial2slotMap is None:
                self.serial2slotMap = newJbodFindSlotNumbers(scsiaddr=sesControllers[1],sortBySerial=True)
        except Exception as e:
            print(e)
            print("Unable to get information about slot to kernel drive mappings in new jbod.")

from pprint import pprint
class storage_jbod_old(storage_jbod):
    def __init__(self,uniqueID,sesControllers=None,disksByEnclosure=None,disksas2serial=None):
        super().__init__(uniqueID=uniqueID,sesControllers=sesControllers,disksByEnclosure=disksByEnclosure)
        try:
            self.serial2slotMap = oldJbodFindSlotNumbers(scsiaddr=self.sesControllers[0],sortBySerial=True,sas2SerialMap=disksas2serial)
            if self.serial2slotMap is None:
                self.serial2slotMap = oldJbodFindSlotNumbers(scsiaddr=sesControllers[1],sortBySerial=True,sas2SerialMap=disksas2serial)
        except Exception as e:
            print(e)
            print("Unable to get information about slot to kernel drive mappings in old jbod.")


class storage_ses(storage_device):
    def __init__(self,uniqueID):
        super().__init__(uniqueID=uniqueID)

class storage_physical_disk(storage_device):
    def __init__(self,serialnumber=None,alogicaldisk=None, index=None,slot=None,smartpopulated=False,nosmart=False):#logical disk is an optional string parameter that is one of the OS logical disks of this hard disk like sde
        if serialnumber is None:
            print("This class requires the serial number of a hard disk.")
            print("Disk identifiers",serialnumber,alogicaldisk)
            with open("/var/log/storageMonitor/storage_info.log",'a') as f:
                f.write("problem creating a hard drive with no serial. check out: ")
                f.write(str(serialnumber))
                f.write(alogicaldisk)
            exit(1)
        super().__init__(uniqueID=serialnumber)
        self.serialnumber = serialnumber
        self.attributes['serialnumber'] = serialnumber
        self.attributes['children'] = []
        self.attributes['slot'] = slot
        self.attributes['index'] = index
        self.smartPopulated = smartpopulated
        if nosmart or self.serialnumber == 'DISKERROR':
            self.smartPopulated = True
        if alogicaldisk is not None:
            self.attributes['children'].append(alogicaldisk)
            if not self.smartPopulated:
                self.getSMART(sdname=alogicaldisk)

    def addChild(self,alogicaldisk):
        self.attributes['children'].append(alogicaldisk)
        self.attributes['children'].sort()

    def getSMART(self, sdname):
        command = ['smartctl', '-a', '--json', '/dev/' + sdname]
        results = errorHandledRunCommand(command=command)
        if results['returncode'] != 0:
            print("There was an error, cannot continue getSMART. See details below\n",
                  "stdout:\n" + results['stdout'],"stderr: \n"+results['stderr'])
            print("The return code was ",results['returncode'])
            jdata = {}
        else:
            data = results['stdout']
            jdata = json.loads(data)
        properties = {}
        try:
            properties['responsetime'] = results['timespent']
        except KeyError:
            properties['responsetime'] = 1000000

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
            ATAproperties = self.getSMARTata(jdata=jdata)
            properties.update(ATAproperties)
            scsiempty = self.getSMARTscsi(jdata={'json_format_version':jdata['json_format_version']})
            properties.update(scsiempty)
        elif properties['protocol'] == 'SCSI':
            scsiproperties = self.getSMARTscsi(jdata=jdata)
            properties.update(scsiproperties)
            ataempty = self.getSMARTata(jdata={'json_format_version':jdata['json_format_version']})
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
        self.smartPopulated = True
        self.attributes.update(properties)


    def getSMARTata(self,jdata={}):
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

    def getSMARTscsi(self,jdata={}):
        try:
            json_format_version = jdata['json_format_version']
            if json_format_version == [1,0]:
                return self.getSMARTscsi10(jdata=jdata)
            elif json_format_version == [2,0]:
                print("I don't know how to parse this json yet. Tell Hancock")
            else:
                return self.getSMARTscsi10(jdata=jdata)
        except KeyError:
            print("Unable to determine json format version. assuming 1,0")
        return self.getSMARTscsi10(jdata=jdata)

    def getSMARTscsi10(self,jdata):
        properties = {}
        try:
            properties['vendor'] = jdata['vendor']
        except KeyError:
            properties['vendor'] = ''
        try:
            properties['model'] = jdata['product']
        except KeyError:
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
            properties['readerroruncorrectedtotal'] = jdata['scsi_error_counter_log']['read']['total_uncorrected_errors']
        except KeyError:
            properties['readerroruncorrectedtotal'] = 0
        try:
            properties['readerrorcorrectedbyreadwrite'] = jdata['scsi_error_counter_log']['read']['errors_corrected_by_rereads_rewrites']
        except KeyError:
            properties['readerrorcorrectedbyreadwrite'] = 0
        try:
            properties['readerrorcorrectedeccfast'] = jdata['scsi_error_counter_log']['read']['errors_corrected_by_eccfast']
        except KeyError:
            properties['readerrorcorrectedeccfast'] = 0
        try:
            properties['readerrorcorrectedeccdelayed'] = jdata['scsi_error_counter_log']['read']['errors_corrected_by_eccdelayed']
        except KeyError:
            properties['readerrorcorrectedeccdelayed'] = 0
            
        try:
            properties['verifyerrorcorrectedtotal'] = jdata['scsi_error_counter_log']['verify']['total_errors_corrected']
        except KeyError:
            properties['verifyerrorcorrectedtotal'] = 0
        try:
            properties['verifyerroruncorrectedtotal'] = jdata['scsi_error_counter_log']['verify']['total_uncorrected_errors']
        except KeyError:
            properties['verifyerroruncorrectedtotal'] = 0
        try:
            properties['verifyerrorcorrectedbyreadwrite'] = jdata['scsi_error_counter_log']['verify']['errors_corrected_by_rereads_rewrites']
        except KeyError:
            properties['verifyerrorcorrectedbyreadwrite'] = 0
        try:
            properties['verifyerrorcorrectedeccfast'] = jdata['scsi_error_counter_log']['verify']['errors_corrected_by_eccfast']
        except KeyError:
            properties['verifyerrorcorrectedeccfast'] = 0
        try:
            properties['verifyerrorcorrectedeccdelayed'] = jdata['scsi_error_counter_log']['verify']['errors_corrected_by_eccdelayed']
        except KeyError:
            properties['verifyerrorcorrectedeccdelayed'] = 0
            
        try:
            properties['writeerrorcorrectedtotal'] = jdata['scsi_error_counter_log']['write']['total_errors_corrected']
        except KeyError:
            properties['writeerrorcorrectedtotal'] = 0
        try:
            properties['writeerroruncorrectedtotal'] = jdata['scsi_error_counter_log']['write']['total_uncorrected_errors']
        except KeyError:
            properties['writeerroruncorrectedtotal'] = 0
        try:
            properties['writeerrorcorrectedbyreadwrite'] = jdata['scsi_error_counter_log']['write']['errors_corrected_by_rereads_rewrites']
        except KeyError:
            properties['writeerrorcorrectedbyreadwrite'] = 0
        try:
            properties['writeerrorcorrectedeccfast'] = jdata['scsi_error_counter_log']['write']['errors_corrected_by_eccfast']
        except KeyError:
            properties['writeerrorcorrectedeccfast'] = 0
        try:
            properties['writeerrorcorrectedeccdelayed'] = jdata['scsi_error_counter_log']['write']['errors_corrected_by_eccdelayed']
        except KeyError:
            properties['writeerrorcorrectedeccdelayed'] = 0
       
            
        return properties

    def exportDictionary(self,properties={}):
        data = {}
        for item in self.attributes:
            try:
                json.dumps(self.attributes[item])
                #data[self.attributes['uniqueID']][item] = self.attributes[item]
                data[item] = self.attributes[item]
            except(TypeError,OverflowError):
                data[item] = str(self.attributes[item])
        data.update(properties)
        firstChild = data['children'][0]
        data['raidpartition'] = getraidpartition(blockName=firstChild)
        data['raidpartitionfriendly'] = getraidpartition(blockName=data['raidpartition'],friendlyname=True)
        data['mpathdev'] = getmpathparent(blockName=firstChild)
        data['mpathdevfriendly'] = getmpathparent(blockName=data['mpathdev'],friendlyname=True)
        return data

class storage_logical_disk(storage_device):
    def __init__(self, sdname=None, scsiaddr=None, serialnumber=None, sasaddress=None, iomoduleSG=None):
        if sdname is None:
            if scsiaddr is None:
                print("This function requires either the SCSI addrress or the block name of a logical disk.")
            else:
                sdname = scsiAddr2BlockDevName(scsiaddr=scsiaddr)[1]
        if sdname is None:
            print("Uanble to create storage_logical_disk for block device",sdname)
            return
        super().__init__(uniqueID=sdname)
        if scsiaddr is None:
            self.attributes['scsiaddr'] = blockDevName2SCSIaddr(blockDevName=sdname)
        else:
            self.attributes['scsiaddr'] = scsiaddr
        if serialnumber is None:
            self.attributes['serialnumber'] = blockDevName2SerialNumber(blockName=sdname)
        else:
            self.attributes['serialnumber'] = serialnumber
        if sasaddress is None:
            self.attributes['sasaddress']  = blockDevName2SASaddr(blockName=sdname)
        else:
            self.attributes['sasaddress'] = sasaddress
        if iomoduleSG is None:
            iomoduleSCSI = scsiDisk2SEScontroller(blockDevName2SCSIaddr(blockDevName=sdname))
            self.attributes['iomodule']  = scsiAddr2SG(iomoduleSCSI)
        else:
            self.attributes['iomodule'] = iomoduleSG
        self.attributes['name'] = sdname

#----------------------------functions-------------------------------------------------

