from hancockStorageMonitor.localgatherers.scsiOperations import errorHandledRunCommand

class lscpuParser(object):
    def __init__(self):
        self.serverProperties = {}
        self.cpuProperties = {}
        self.lscpuUTF8data = errorHandledRunCommand(command=['lscpu'])
        if self.lscpuUTF8data is None or self.lscpuUTF8data['returncode'] > 0:
            print("Could not get data from lscpu")
        else:
            self.lscpuUTF8data = self.lscpuUTF8data['stdout'].splitlines()
            self.serverPropertyNames = ['numsockets','numtotalthreads','']
            self.cpuProperties = {}
            self.integerProperties = ['threadspercore','numcores','numsockets','numtotalthreads']
            self.floatProperties = ['bogomips','cpufreqmhz',]
            self.importantProperties = {'architecture':'architecture','bogomips':'bogomips','byte order':'byteorder','core(s) per socket':'numcores','cpu mhz':'cpufreqmhz',
                                        'cpu op-mode(s)':'opmodes','cpu(s)':'numtotalthreads','l1d cache':'l1dcache','l1i cache':'l1icache','l2 cache':'l2cache','l3 cache':'l3cache','model name':'model',
                                        'socket(s)':'numsockets','thread(s) per core':'threadspercore','vendor id':'vendor','virtualization':'virtualization'}
            for item in self.lscpuUTF8data:
                properties = item.split(':')[0].strip().lower()
                if properties in self.importantProperties:
                    propertyDB = self.importantProperties[properties]
                    if propertyDB in self.integerProperties:
                        value = int(item.split(':')[1].strip().lower())
                    elif propertyDB in self.floatProperties:
                        value = float(item.split(':')[1].strip().lower())
                    else:
                        value = item.split(':')[1].strip().lower()
                    if propertyDB in self.serverPropertyNames:
                        self.serverProperties[propertyDB] = value
                    else:
                        self.cpuProperties[propertyDB] = value
                else:
                    continue
    def exportDictionary(self,properties={}):
        data = {self.cpuProperties['model']:self.cpuProperties}
        data[self.cpuProperties['model']].update(properties)
        return data