from hancockStorageMonitor.localgatherers.storage_info import storage_info
from pprint import pprint, pformat
from hancockStorageMonitor.localgatherers.scsiOperations import blockDevName2SerialNumber, getMDparent, errorHandledRunCommand
from hancockStorageMonitor.localgatherers.scsiOperations import getmpathparent, getraidpartition
from hancockStorageMonitor.colorama import Fore, Back, Style
from contextlib import contextmanager,redirect_stderr,redirect_stdout
from os import system
from hancockStorageMonitor.common.displays import selectmenu, showdisks
from time import sleep

# Optional parameters include info = storage_info() class object and xdata = storage_info().exportDictionary()
def manualDiskSelection(innerinfo=None,innerxdata=None):
    diskSerial = None
    if innerinfo is None:
        innerinfo = storage_info()
    if innerxdata is None:
        innerxdata = innerinfo.exportDictionary(write=False)
    print(Fore.CYAN)
    print(Style.BRIGHT)
    print("This function is not yet implemented. Check back later.")
    print(Style.RESET_ALL)
    return diskSerial

def removeFromMDRAID(blockDevName,info,force=False):
    # Function to take any block devices that corresponding to a disk and remove it from an MD device if it is part of one.
    # parameter info requires an instance of storage info class.
    # If the force parameter is False, the device will not be removed unless it is "faulty"
    # If the force parameter is True the device will be first be set to Fault if not already, then removed.
    mdname = getMDparent(blockName=blockDevName)
    if mdname is None:
        print("Not part of md device")
        print("no changes made")
        return None

    command = ['mdadm','-r','/dev/'+mdname,'/dev/'+blockDevName]
    errorHandledRunCommand(command=command)

def removalmenu(info):
    print("Type of data received by removalmenu",type(info))

    remmenu = selectmenu(title="Disk Removal Menu")
    print("contents of remmenu ",remmenu.menuitems)
    input("Strike a key to continue in removalmenu")
    remmenu.addmenuitem(key="Show Disk Information",value=showdisks,
                        data={'info':info,'colors':{'sep':"BLUE",'header':"WHITE",'clabel':"WHITE",'normal':"GREEN"},
                              'highlights':{'None':"LIGHTRED_EX",'Error':"RED",'missing':"RED",'Missing':"RED"}})
    remmenu.addmenuitem(key="Select disk for removal from likely list.",value=print)
    remmenu.addmenuitem(key="Manually select disk from all disks.",value=print)
    print(remmenu.menuitems)
    sleep(10)
    remmenu.displaymenu()

def main():
    #  Suppress any console output from storage_info() class instantiation by redirecting the stdout pipe to /dev/null
    with redirect_stdout(open('/dev/null','w')):
        info = storage_info()
    # Create the showdisks menu.
    mainmenu = selectmenu(title="Main Disk Operations Menu",autosort=False)

    mainmenu.addmenuitem(key='Prepare a disk for removal.',value=removalmenu,data={'info':info})
    mainmenu.addmenuitem(key='Add new disk to RAID array.',value=print)
    mainmenu.displaymenu()

    # dumpdata = info.exportDictionary(write=False)
    # faults = {}
    # for uuid in dumpdata['raidarrays']:
    #     for member in dumpdata['raidarrays'][uuid]['members']:
    #         if dumpdata['raidarrays'][uuid]['members'][member]['memberstate'] not in ['in_sync','spare']:
    #             serialnumber = blockDevName2SerialNumber(member)
    #             faults[serialnumber] = {'pname':member,'raidarraystate':dumpdata['raidarrays'][uuid]['members'][member]['memberstate'],'mdname':dumpdata['raidarrays'][uuid]['name']}
    #             faults[serialnumber].update(dumpdata['harddrives'][serialnumber])
    #             faults[serialnumber]['problem'] = 'RAID partition '+faults[serialnumber]['pname']+' at index '+str(faults[serialnumber]['index'])+\
    #                                               ' of JBOD chassis '+str(faults[serialnumber]['chassisSerial'])+' with logical disks '+str(faults[serialnumber]['children'])+\
    #                                               ' shows '+faults[serialnumber]['raidarraystate']+' in a RAID array '+str(faults[serialnumber]['mdname'])
    #
    # for serialnumber in dumpdata['harddrives']:
    #     if dumpdata['harddrives'][serialnumber]['mdparent'] is None:
    #         faults[serialnumber] = dumpdata['harddrives'][serialnumber]
    #         faults[serialnumber]['mdname'] = None
    #         faults[serialnumber]['problem'] = 'SAS Disk at index '+str(faults[serialnumber]['index'])+' of JBOD chassis '+str(faults[serialnumber]['chassisSerial'])+' with logical disks '+str(faults[serialnumber]['children'])+' is not part of a RAID array.'
    # if len(faults) == 0:
    #     print("There are no detectable faulty disks on this system. Please proceed manually.")
    #     choices = {}
    #     exit(0)
    # else:
    #     choices = {}
    # choices = [item for item in faults]
    # system("clear\n")
    # print("\n\n\n\n\n\n\n\n\n")
    # while True:
    #     try:
    #         print(Fore.GREEN,"The following disks appear to be likely removal targets.")
    #         print(Fore.YELLOW)
    #         for choice in choices:
    #             print('\n', choices.index(choice), ':', faults[choice]['problem'])
    #         print("\n",Fore.BLUE+str(len(choices)),': None of these. Select from all disks.')
    #         print(Style.RESET_ALL)
    #         userpick = int(input("\nPlease select a number from above.\n\n"))
    #         if -1 < userpick < len(choices)+1:
    #             break
    #         else:
    #             raise ValueError
    #     except ValueError:
    #         system("clear\n")
    #         print(Fore.RED+"\n\n\n\n\n\nThat is not a valid choice from this menu. Please try again.\n")
    #         print(Style.RESET_ALL)
    #     except Exception as e:
    #         system("clear\n")
    #         print(Fore.RED+"Unknown error please choose again.")
    #         print(e)
    #         print(Style.RESET_ALL)
    # try:
    #     target = choices[userpick]
    # except IndexError:
    #     # user must have chosen to manually select from all disks. Launch function to do this.
    #     target = manualDiskSelection(innerinfo=info,innerxdata=dumpdata)
    # except Exception as e:
    #     print(Fore.RED + "Unknown error please try again.")
    #     print(e)
    #     print(Style.RESET_ALL)
    #     target = None
    #
    # print("\nYou have chosen target:")
    # validDiskDevices = ['logicaldisks','multipaths','raidpartitions','harddrives']
    # if target is not None:
    #     pprint(dumpdata['harddrives'][target])
    #     try:
    #         targettype = info.name2type[target]
    #         if targettype not in validDiskDevices:
    #             raise Exception("I don't know how to remove this sort of device."+str(targettype))
    #     except KeyError as k:
    #         print(k)
    #         print("I don't know how to remove this sort of devices.")
    #     except Exception as e:
    #         print(e)
    #         exit(1)
    # else:
    #     print("No valid target selected. GOODBYE\n")
    #     exit(1)
    #
    # #So now we will use the target type to handle removal.

main()


