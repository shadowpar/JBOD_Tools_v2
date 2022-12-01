from hancockStorageMonitor.localgatherers.storage_info import storage_info
from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand
from pathlib import Path
from os import getuid, readlink
from pprint import pprint
from platform import node
from time import sleep
maxsize = 21
if getuid() != 0:
    print("This program must be run as root.")
    exit(1)
# cProfile.run("storage_info(quick=True)")
# exit(1)
print("--------------------Step 5-------------------------")
info = storage_info()
if len(info.raidarrays) != 0:
    print("Detected md RAID arrays on host. Cannot continue safely.")
    exit(1)
print("--------------------Step 6-------------------------")
chassis = [chassis for chassis in info.harddrivesByChassis]
chassis = {chassis.index(serial):serial for serial in chassis}
if len(chassis) > 1:
    while True:
        print("Please select a chassis to create RAID arrays from the following list.")
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
raidlevels = ['RAID5','RAID6']
while True:
    print("There is a total of",len(targets),"disks that can be added to RAID arrays in this chassis.\n")
    for item in raidlevels:
        print(raidlevels.index(item),':',item,"\n")
    choice = input("Please choose a RAID level by selecting an item from the list.\n")
    try:
        choice = int(choice)
        raidlevel = raidlevels[choice]
        break
    except Exception:
        print("That is not a valid choice. Please try again.\n")
print("--------------------Step 9-------------------------")
choices = {}
if raidlevel == 'RAID6':
    for disksperarray in range(4,len(targets)):
        spares = int(len(targets)%disksperarray)
        numarray = int((len(targets) - spares)/disksperarray)
        lunsize = (float(exDriveCapacity)*(disksperarray -2))/1000/1000/1000/1000 #capacity of a LUN after removing parity in Terabytes.
        choices[disksperarray] = {'spares':spares,'numarray':numarray, 'lunsize':lunsize}
elif raidlevel == 'RAID5':
        for disksperarray in range(3,len(targets)):
            spares = int(len(targets)%disksperarray)
            numarray = int((len(targets) - spares)/disksperarray)
            lunsize = (float(exDriveCapacity)*(disksperarray -1))/1000/1000/1000/1000 #capacity of a LUN after removing parity in Terabytes.
            choices[disksperarray] = {'spares':spares,'numarray':numarray, 'lunsize':lunsize}
print("--------------------Step 10-------------------------")

while True:
    print("Please choose how many devices per LUN from among the following possible",raidlevel,"configurations.")
    for config in choices:
        if int(config < maxsize):
            print("\n",config," disk per LUN. Total of",choices[config]['numarray'],"LUNS ",choices[config]['lunsize'],"TB each with ",choices[config]['spares'],"hot spares.")
    choice = input("Select a number of disks in one LUN\n")
    try:
        choice = int(choice)
        temp = choices[choice]
        break
    except Exception:
        print("That is not a valid choice. Please try again.\n")
print("--------------------Step 11-------------------------")
while True:
    print("You have chosen:\n")
    print(choice,"disks per LUN. For a total of",choices[choice]['numarray'],"LUNS of size",choices[choice]['lunsize'],"TB with",choices[choice]['spares'],"hot spares.\n")
    print("It is time to create the arrays. This will result in all data on the selected drives being destroyed.\n")
    certain = input("\nAre you certain you want to do this? Type 'yes' or 'no'\n")
    if certain.lower() in ['yes','no','y','n']:
        break
    else:
        print("That is not a valid answer. Please try again.\n")
# pprint(targets)
targets = list(targets.values())
print("--------------------Step 12-------------------------")
# pprint(targets)
numperarray = choice
numarray = int(choices[choice]['numarray'])
numspares = int(choices[choice]['spares'])
rdlevel = str(raidlevel[-1:])
sparelist = targets[-numspares:]
targets = targets[:-numspares]
alldisks = targets
alldisks.extend(sparelist)
#now we partition the disks to prepare them to become part of RAID arrays
print("--------------------Step 13-------------------------")
for target in alldisks:
    command = ['parted','-s','/dev/'+target,'mklabel','gpt']
    print("Running command", command)
    # result = {'returncode':0}
    result = errorHandledRunCommand(command=command)
    if result is None or result['returncode'] != 0:
        print("\nI encountered an error while trying to create partition table on /dev/"+target)
        print("\nI cannot continue.")
        exit(1)
    else:
        command = ['parted','-s','/dev/'+target,'-a','optimal','unit','MB','mkpart','primary','1','100%','set','1','hidden','on']
        print("Running command", command)
        result = errorHandledRunCommand(command=command)
        if result is None or result['returncode'] != 0:
            print("\nI encountered an error while trying to create partition on /dev/"+target)
            print("\nI cannot continue.")
            exit(1)
#flush multipath maps
print("--------------------Step 14-------------------------")
command = ['multipath','-F']
print("Running command",command)
# result = {'returncode':0}
result = errorHandledRunCommand(command=command)
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to flush the multipath maps.")
    print("\nI cannot continue.")
    exit(1)
print("--------------------Step 15-------------------------")
#Rebuild multipath maps.
command = ['multipath']
print("Running command",command)
# result = {'returncode':0}
result = errorHandledRunCommand(command=command)
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to rebuild the multipath maps.")
    print("\nI cannot continue.")
    exit(1)
print("--------------------Step 16-------------------------")
# Create a dictionary of sd disk names to their multipath raid partition dm names.
sleep(20) #Giving the OS time to create all the new dm devices after running multipath.
try:
    newinfo = storage_info()
except KeyError as k:
    print(k)
    print("Problem running storage info")
    exit(1)
print("survived storage_info")
dmmpath2dmpart = {}
sdname2dmpart = {}
for part in newinfo.dm_partitions:
    mpathname = newinfo.dm_partitions[part].attributes['children'][0]
    dmmpath2dmpart[mpathname] = part
print("--------------------Step 17-------------------------")
for dmmpath in dmmpath2dmpart:
    for sdname in newinfo.multipaths[dmmpath].attributes['children']:
        partname = dmmpath2dmpart[dmmpath]
        sdname2dmpart[sdname] = partname
print("--------------------Step 18-------------------------")
print("before and after")
# print(targets)
# print(sparelist)
# pprint(sdname2dmpart)
#now all disks in targets have a gpt partition table and a hidden parition called 1.
targets = [(sdname2dmpart[target] if target in sdname2dmpart else target) for target in targets]
print("--------------------Step 19-------------------------")
sparelist = [(sdname2dmpart[spare] if spare in sdname2dmpart else spare) for spare in sparelist]
print("--------------------Step 20-------------------------")
print(targets)
print(sparelist)


#now we chop up the list of non spare disks into LUNs
luns = {'md'+str(count):[] for count in range(0,numarray)}

for mdcount in luns:#chop up targets into lun size lists in keyed to md names.
    while len(luns[mdcount]) < numperarray:
        luns[mdcount].append(targets.pop(0))
pprint(luns)
print("--------------------Step 21-------------------------")
for lun in luns:
    command = ['mdadm','-v','--create','/dev/'+lun,'--level='+rdlevel,'--raid-devices='+str(numperarray),'--bitmap=/bitmap/'+str(lun)]
    command.extend(['/dev/'+str(target) for target in luns[lun]]) # add all the devices for the LUN
    print("Running command", command)
    # result = {'returncode':0}
    result = errorHandledRunCommand(command=command)
    if result is None or result['returncode'] != 0:
        print("\nI encountered an error while trying to create the md device:",lun)
        print("\nI cannot continue.")
        exit(1)
print("--------------------Step 22-------------------------")
#now we will create the mdadm.conf file
mdadmpath = Path('/etc').joinpath('mdadm.conf')
if not mdadmpath.is_file():
    mdadmpath.touch()
mdadmpath.write_text("MAILFROM "+str(node())+"\nMAILADDR raid_admin\nDEVICE /dev/dm*\n")
command = ['mdadm','-D','--scan']
print("Running command",command)
# result = {'returncode':0,'stdout':'put md devices here.\n'}
result = errorHandledRunCommand(command=command)
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to create mdadm.conf by running",command)
    print("\nI cannot continue.")
    exit(1)
else:
    with mdadmpath.open('a') as f:
        output = result['stdout'].splitlines()
        output = [item.strip()+" spare-group=global\n" for item in output]
        for line in output:
            f.write(line)
print("--------------------Step 23-------------------------")
#Now we add the spares to md0. Any array can use them though.
md0path = Path('/sys/block/md0')
if md0path.is_symlink():
    command = ['mdadm','--add-spare','/dev/md0']
    command.extend('/dev/'+item for item in sparelist)
    print(command)
    result = errorHandledRunCommand(command=command)
    if result is None or result['returncode'] != 0:
        print("\nI encountered an error while trying to add the spares to md0 by running",command)
print("--------------------Step 24-------------------------")
#Now we run dracut -f to add mdadm.conf to sys image.
command = ['dracut','-f']
print("Running command",command)
# result = {'returncode':0}
result = errorHandledRunCommand(command=command)
if result is None or result['returncode'] != 0:
    print("\nI encountered an error while trying to update sysimage by running",command)
    print("\nI cannot continue.")
    exit(1)
#Now for convenience, show the contents of /proc/mdstat
print("--------------------Step 25-------------------------")
with open('/proc/mdstat','r') as f:
    print(f.read())
print("RAID creation complete")
