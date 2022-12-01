from hancockStorageMonitor.localgatherers.lscpuParser import lscpuParser
from pathlib import Path
from pprint import pformat
from re import search
from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand

#  The attributes of this class must be mapped to the headnodes class im sqlalchemy_classes
class serverInfo(object):
    def __init__(self):
        self.attributes = {}
        self.name = self.attributes['name'] =  Path('/etc/hostname').read_text().strip()
        self.model = ''
        self.datacenter = ''
        self.rack = ''
        self.slot = ''
        self.serialnumber = ''
        self.numsockets = ''
        self.numtotalthreads = ''
        self.serialnumber = None
        self.haszfs = False
        self.hasdmraid = False
        self.checkMassStorage()
        self.dmidata = self.getDMIdata()
        self.cpu_data = lscpuParser()
        self.getAttributes()
        #self.cpu = cpuInfo(cpuProperties=self.cpu_data.cpuProperties)

    def getDMIdata(self):
        # First we get a list of all keywords supported by dmidecode -s
        dmidata = {}
        command = ['dmidecode','-s']
        result = errorHandledRunCommand(command=command)
        if result is not None and result['returncode'] == 2:
            print(result['stdout'])
            output = result['stderr'].splitlines()
            print(output)
        else:
            print(result)
            print("There was an error inside getDMIdata inside serverInfo class.")
            return dmidata
        output = [item.strip() for item in output if '-' in item]
        for item in output:
            command = ['dmidecode','-s',item]
            result = errorHandledRunCommand(command=command)
            if result is not None and result['returncode'] == 0:
                dmidata[item] = result['stdout'].strip()
            else:
                print("Failed to fetch dmidecode -s",item)
                dmidata[item] = None
        return dmidata

    def getAttributes(self):
        translator = {'chassis-serial-number':'serialnumber','product_name':'model'}
        serverInfoPath = Path('/sys/devices/virtual/dmi/id')
        attrs = {keyname.name:keyname.read_text().strip() for keyname in list(serverInfoPath.iterdir()) if keyname.is_file()}
        for attr in attrs:
            if attr in translator:
                self.attributes[translator[attr]] = attrs[attr]
            else:
                self.attributes[attr] = attrs[attr]
        for attr in self.dmidata:
            if attr in translator:
                self.attributes[translator[attr]] = self.dmidata[attr]
            else:
                self.attributes[attr] = self.dmidata[attr]
        if self.attributes['serialnumber'] is None or self.attributes['serialnumber'].strip() == '':
            self.attributes['serialnumber'] = self.attributes['product_serial']

        self.attributes['datacenter'] = self.datacenter = 'error'
        self.attributes['rack'] = self.rack = 'error'
        self.attributes['slot'] = self.slot = -1
        self.guessExperiment()
        self.attributes['numsockets'] = self.numsockets = self.cpu_data.serverProperties['numsockets']
        self.attributes['numtotalthreads'] = self.numtotalthreads = self.cpu_data.serverProperties['numtotalthreads']
        self.attributes['cpumodel'] = self.cpu_data.cpuProperties['model']
        self.attributes['hasmdraid'] = self.hasdmraid
        self.attributes['haszfs'] = self.haszfs
        for data in self.dmidata:
            if data in translator:
                self.attributes[translator[data]] = self.dmidata[data]
            else:
                self.attributes[data] = self.dmidata[data]

    def checkMassStorage(self):
        #check if zfs has pools.
        try:
            command = ['zpool','status']
            result = errorHandledRunCommand(command=command)
            if result is None:
                self.haszfs = False
            else:
                self.haszfs = True
        except Exception as e:
            print("Not ZFS server.")
            self.haszfs = False
        # Check if mdraid is in use.
        command = ['mdadm','-D','--scan']
        result = errorHandledRunCommand(command=command)
        if result is None:
            self.hasdmraid = False
        elif len(result['stdout']) > 0:
            self.hasdmraid = True
        else:
            self.hasdmraid = False

    def guessExperiment(self):
        atlasResult = search(r'^dc.*\.usatlas\.bnl\.gov',self.name)
        if atlasResult:
            self.attributes['experiment'] = 'atlas'
            return
        belleResult = search(r'^dcbl.*\.sdcc\.bnl\.gov', self.name)
        if belleResult:
            self.attributes['experiment'] = 'belle2'
            return
        if self.name.split('.')[0] in ['qgp004','qgp006','qgp100','qgp101','qgp102','qgp103','qgp104','qgp105']:
            self.attributes['experiment'] = 'phenix'
            return
        if self.name.split('.')[0] in ['qgp001','qgp002','qgp003','qgp005']:
            self.attributes['experiment'] = 'star'
            return
        if 'dcsph' in self.name.split('.')[0]:
            self.attributes['experiment'] = 'sphenix'
        else:
            self.attributes['experiment'] = 'unknown'

    def __repr__(self):
        result = str(type(self))
        result = result+"\n"+"My Attributes:"
        result = result+"\n"+pformat(self.attributes)
        return result
    def exportDictionary(self,properties={}):
        data = {self.name:self.attributes,'cpu_data':self.cpu_data.exportDictionary(properties={'hostname':self.name})}
        data[self.name].update(properties)
        return data

