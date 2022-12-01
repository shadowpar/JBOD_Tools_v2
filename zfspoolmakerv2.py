from hancockStorageMonitor.localgatherers.storage_info import storage_info
from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand, multiExecuteExternal
from pathlib import Path
from os import getuid, readlink
from pprint import pprint
from platform import node
from time import sleep
maxsize = 21
if getuid() != 0:
    print("This program must be run as root.")
    exit(1)


print("--------------------Step 5-------------------------")
info = storage_info()
# if len(info.raidarrays) != 0:
#     print("Detected md RAID arrays on host. Cannot continue safely.")
#     exit(1)
print("--------------------Step 6-------------------------")
chassis = [chassis for chassis in info.harddrivesByChassis]
chassis = {chassis.index(serial):serial for serial in chassis}
if len(chassis) > 1:
    while True:
        print("Please select a chassis to create a ZFS pool from the following list.")
        for entry in chassis:
            print(entry,':',chassis[entry])
        try:
            choice = int(input())
            if choice in chassis:
                chosenChassis = choice
                break
            else:
                print("please only enter a number from the list")
        except ValueError:
            print("please only enter a number from the list")
else:
    chosenChassis = 0
chosenChassis = chassis[chosenChassis]
print("--------------------Step 7-------------------------")
targets = {}
exDriveCapacity = None
for serial in  info.harddrivesByChassis[chosenChassis]:
    if exDriveCapacity is None: exDriveCapacity = info.harddrivesByChassis[chosenChassis][serial].attributes['capacity']
    index = int(info.harddrivesByChassis[chosenChassis][serial].attributes['index'])
    firstld = info.harddrivesByChassis[chosenChassis][serial].attributes['children'][0]
    targets[index] = firstld
targets = {key:targets[key] for key in sorted(targets)}
print("--------------------Step 8-------------------------")
raidlevels = ['raidz1','raidz2','raidz3']
while True:
    print("There is a total of",len(targets),"disks that can be added to a zpool in this chassis.\n")
    for item in raidlevels:
        print(raidlevels.index(item),':',item,"\n")
    choice = input("Please choose a RAID level for each vdev by selecting an item from the list.\n")
    try:
        choice = int(choice)
        raidlevel = raidlevels[choice]
        break
    except Exception:
        print("That is not a valid choice. Please try again.\n")
print("--------------------Step 9-------------------------")
choices = {}
if raidlevel == 'raidz3':
    for disksperarray in range(5,len(targets)):
        spares = int(len(targets)%disksperarray)
        numarray = int((len(targets) - spares)/disksperarray)
        lunsize = (float(exDriveCapacity)*(disksperarray -3))/1000/1000/1000/1000 #capacity of a LUN after removing parity in Terabytes.
        choices[disksperarray] = {'spares':spares,'numarray':numarray, 'lunsize':lunsize}
if raidlevel == 'raidz2':
    for disksperarray in range(4,len(targets)):
        spares = int(len(targets)%disksperarray)
        numarray = int((len(targets) - spares)/disksperarray)
        lunsize = (float(exDriveCapacity)*(disksperarray -2))/1000/1000/1000/1000 #capacity of a LUN after removing parity in Terabytes.
        choices[disksperarray] = {'spares':spares,'numarray':numarray, 'lunsize':lunsize}
elif raidlevel == 'raidz1':
        for disksperarray in range(3,len(targets)):
            spares = int(len(targets)%disksperarray)
            numarray = int((len(targets) - spares)/disksperarray)
            lunsize = (float(exDriveCapacity)*(disksperarray -1))/1000/1000/1000/1000 #capacity of a LUN after removing parity in Terabytes.
            choices[disksperarray] = {'spares':spares,'numarray':numarray, 'lunsize':lunsize}
print("--------------------Step 10-------------------------")

while True:
    print("Please choose how many hard drives per vdev from among the following possible",raidlevel,"configurations.")
    for config in choices:
        if int(config < maxsize):
            print("\n",config," disk per vdev. Total of",choices[config]['numarray'],"LUNS ",choices[config]['lunsize'],"TB each with ",choices[config]['spares'],"hot spares.")
    choice = input("Select a number of disks in one vdev\n")
    try:
        choice = int(choice)
        temp = choices[choice]
        break
    except Exception:
        print("That is not a valid choice. Please try again.\n")
while True:
    print("\nYou must now choose a name for your zpool. This willl automatically be mounted at /{chosen name}\n")
    zpoolname = input("\nPlease type desired zpool name:\n")
    newmountpath = Path('/').joinpath(zpoolname)
    if newmountpath.exists():
        print("I'm sorry but this name cannot be used because /"+zpoolname,"already exists. Please choose another name or delete this directory first.")
        continue
    else:
        break


print("--------------------Step 11-------------------------")
while True:
    print("You have chosen to create a zpool called:",zpoolname,".\n")
    print(choice,"disks per vdev. For a total of",choices[choice]['numarray'],"vdevs of size",choices[choice]['lunsize'],"TB with",choices[choice]['spares'],"hot spares.\n")
    print("It is time to create the pools and vdevs. This will result in all data on the selected drives being destroyed.\n")
    certain = input("\nAre you certain you want to do this? Type 'yes' or 'no'\n")
    if certain.lower() in ['yes','y']:
        break
    elif certain.lower() in ['no','n']:
        print("User has chosen not to contiue.")
        exit(1)
    else:
        print("That is not a valid answer. Please try again.\n")
# pprint(targets)
targets = list(targets.values())
print("--------------------Step 12-------------------------")
# pprint(targets)
numperarray = choice
numarray = int(choices[choice]['numarray'])
numspares = int(choices[choice]['spares'])
rdlevel = str(raidlevel)
sparelist = targets[-numspares:]
targets = targets[:-numspares]
alldisks = targets
alldisks.extend(sparelist)

sdname2dmmpath = {}
for dmmpath in info.multipaths:
    sdnames = info.multipaths[dmmpath].attributes['children']
    for child in sdnames:
        if child in targets or child in sparelist:
            sdname = child
            sdname2dmmpath[sdname] = dmmpath
sdname2dmmpath = {}
targets = [(sdname2dmmpath[target] if target in sdname2dmmpath else target) for target in targets]
print("--------------------Step 19-------------------------")
sparelist = [(sdname2dmmpath[spare] if spare in sdname2dmmpath else spare) for spare in sparelist]
print("--------------------Step 20-------------------------")
print(targets)
print(sparelist)


#now we chop up the list of non spare disks into vdevs
vdevs = {'vdev'+str(count):[] for count in range(0,numarray)}

for vdev in vdevs:#chop up targets into lun size lists in keyed to md names.
    while len(vdevs[vdev]) < numperarray:
        vdevs[vdev].append(targets.pop(0))
pprint(vdevs)
command = ['zpool','create',zpoolname]
for vdev in vdevs:
    comm = [rdlevel]
    for dm in vdevs[vdev]:
        comm.append('/dev/'+dm)
    command.extend(comm)
if len(sparelist) > 0:
    command.append('spare')
    for spare in sparelist:
        command.append('/dev/'+spare)
pprint(command)
commandString = ''
for item in command:
    commandString = commandString+item+' '
print(commandString)
result = errorHandledRunCommand(command=command,timeout=120)
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to create the ZFS pool",zpoolname)
    print("\nI cannot continue.")
    exit(1)
command = ['zfs','set','recordsize=1M',zpoolname]
result = errorHandledRunCommand(command=command,timeout=120)
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to set recordsize to 1M for ",zpoolname)
    print("\nI cannot continue.")
    exit(1)
print("\nYour zpool named",zpoolname,"has been created sucessfully.\n")
print("Remember this program does not add zil logs or l2arc cache. Please do this manually.\n")
print("You can view the status of your new zpool with the command 'zpool status "+zpoolname+"'\n")



