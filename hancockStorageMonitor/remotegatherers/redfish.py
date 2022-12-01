import requests
import json
from pprint import pprint
import socket
import time
import asyncio
import base64

def send_data_point(metric,value):
    monitor_server_name = 'graphite.sdcc.bnl.gov'
    port = int(2003)
    #buffer_size = 1024
    message = metric+' '+str(value)+' '+str(int(time.time()))+"\n"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((monitor_server_name,port))
        print(message)
        s.send(message.encode('utf-8'))
        s.close()
    except Exception as e:
        print("Error sending data")
        print(e)
        s.close()

class dellServerRedfish(object):
    def __init__(self, managementInterfaceName,proxy=False):
        self.mgtInterface = managementInterfaceName
        self.authCookie = None
        self.sessionLocation = None
        if proxy:
            self.proxies = {'http': 'socks5h://127.0.0.1:8976', 'https': 'socks5h://127.0.0.1:8976'}
        else:
            self.proxies = None
        self.getAuthCookie()
        self.infoTargets = {'general':'/redfish/v1/Chassis/System.Embedded.1','network':'/redfish/v1/Systems/System.Embedded.1/EthernetInterfaces','storage':'/redfish/v1/Systems/System.Embedded.1/Storage'}
        self.data = {}
        self.targetProcessors = {'general':self.processChassisGeneral,'network':self.processNetwork,'storage':self.processStorage}
        for item in self.infoTargets:
            data = self.getTargetJSONInfo(self.infoTargets[item])
            self.targetProcessors[item](data=data)
        self.endSession()
        pprint(self.data)
    def processChassisGeneral(self,data={}):
        self.data['general'] = data
        return

    def processNetwork(self,data={}):
        if data is None:
            return
        self.data['network'] = {}
        for interface in data['Members']:
            path = interface['@odata.id']
            name = path.split('/')[-1]
            self.data['network'][name] = self.getTargetJSONInfo(target=path)
        return

    def processStorage(self,data={}):
        if data is None:
            return
        self.data['storage'] = {}
        for storageDev in data['Members']:
            path = storageDev['@odata.id']
            name = path.split('/')[-1]
            self.data['storage'][name] = self.getTargetJSONInfo(target=path)
            self.data['storage'][name]['disks'] = {}
            for disk in self.data['storage'][name]['Drives']:
                diskpath = disk['@odata.id']
                diskname = diskpath.split('/')[-1]
                self.data['storage'][name]['disks'][diskname] = self.getTargetJSONInfo(target=diskpath)

        return


    def getTargetJSONInfo(self,target):
        if target in self.infoTargets:
            target = self.infoTargets[target]
        url = 'https://'+self.mgtInterface+target
        headers = {'content-type': 'application/json','X-Auth-Token': self.authCookie}
        response = requests.get(url=url,verify=False,headers=headers,proxies=self.proxies)
        if response.status_code != 200:
            print("There was an error with the web page")
            print(response.status_code)
            print(response.content)
            return None
        else:
            return response.json()

    def getAuthCookie(self):
        pds = 'QkMkc2R3NEw='
        creds = {"UserName":"root","Password":""}
        url = 'https://'+self.mgtInterface+'/redfish/v1'
        print("The url for auth cookie is ",url)
        headers = {'content-type': 'application/json'}
        r = requests.get(url=url,verify=False,headers=headers,proxies=self.proxies)
        if r.status_code != 200:
            return None
        else:
            print("here at else the status code is ",r.status_code)
            sessionTarget = r.json()
            pprint(sessionTarget)
            sessionTarget = sessionTarget['Links']['Sessions']['@odata.id']
            pprint(sessionTarget)
            url = 'https://'+self.mgtInterface+sessionTarget
            sr = requests.post(url=url,data=json.dumps(creds),headers=headers,verify=False,proxies=self.proxies)
            if sr.status_code != 201:
                print("There was an issue creating the session on target",url+sessionTarget)
                print(sr.content)
                return None
            else:
                data = sr.json()
                headdata = sr.headers
                token = headdata['X-Auth-Token']
                sessionLocation = headdata['Location']
                self.authCookie = token
                self.sessionLocation = sessionLocation
    def endSession(self):
        url = 'https://'+self.mgtInterface+self.sessionLocation
        headers={'content-type': 'application/json','X-Auth-Token': self.authCookie}
        r = requests.delete(url=url,headers=headers,verify=False,proxies=self.proxies)


    def setTargetJSONInfo(self,target,jsonInfo):
        pass

class ultrastar102redfish(object):
    def __init__(self, managementInterfaceName,experiment, creds=('admin','admin'), proxy=False):
        self.mgtInterface = managementInterfaceName
        self.upload_data = {}
        self.experiment = experiment
        self.jbodname = managementInterfaceName.split('iom')[0]
        self.iomname = 'iom'+managementInterfaceName.split('.')[0].split('iom')[1]
        print("my jbod name is ",self.jbodname)
        self.authCookie = None
        self.creds = creds
        if proxy:
            self.proxies = {'http': 'socks5h://127.0.0.1:8976','https': 'socks5h://127.0.0.1:8976'}
        else:
            self.proxies = None
        self.sessionLocation = None
        self.infoTargets = {'entry':'/redfish/v1','thermal':'/redfish/v1/chassis/enclosure/Thermal','power':'/redfish/v1/Chassis/Enclosure/Power'}
        self.data = {}
        self.targetProcessors = {}

    def begin(self):
        self.getAuthCookie()
        for item in self.infoTargets:
            data = self.getTargetJSONInfo(self.infoTargets[item])
            if item in self.targetProcessors:
                self.targetProcessors[item](data=data)
            else:
                self.data[item] = data
        self.extract_power_data()
        self.extract_temperature_data()
        self.publishGrafana()
        if self.sessionLocation is not None:
            self.endSession()

    def publishGrafana(self):
        for reading in self.upload_data:
                metric_string = 'storage.' + self.experiment + '.' + self.jbodname + '.' + self.iomname + '.' + reading
                value_string = str(self.upload_data[reading])
                print("I am sending metric", metric_string, "and with value", value_string, "to the Grafana server.")
                #send_data_point(metric=metric_string, value=value_string)

    def getTargetJSONInfo(self,target):
        if target in self.infoTargets:
            target = self.infoTargets[target]
        url = 'https://'+self.mgtInterface+target
        if self.authCookie is not None:
            headers = {'content-type': 'application/json','X-Auth-Token': self.authCookie}
            response = requests.get(url=url,verify=False,headers=headers,proxies=self.proxies)
        else:
            headers = {'content-type': 'application/json'}
            response = requests.get(url=url,verify=False,headers=headers,auth=self.creds,proxies=self.proxies)
        if response.status_code != 200:
            print("There was an error with the web page")
            print(response.status_code)
            print(response.content)
            return None
        else:
            return response.json()

    def getAuthCookie(self):
        creds = {"UserName":"admin","Password":"admin"}
        url = 'https://'+self.mgtInterface+'/redfish/v1'
        print("The url for auth cookie is ",url)
        headers = {'content-type': 'application/json'}
        r = requests.get(url=url,verify=False,headers=headers,proxies=self.proxies)
        if r.status_code != 200:
            return None
        else:
            print("here at else the status code is ",r.status_code)
            sessionTarget = r.json()
            pprint(sessionTarget)
            try:
                sessionTarget = sessionTarget['Links']['Sessions']['@odata.id']
            except KeyError as k:
                print(k)
                print("No sessions implementation. Falling back to basic authorization header.")
                return None
            pprint(sessionTarget)
            url = 'https://'+self.mgtInterface+sessionTarget
            sr = requests.post(url=url,data=json.dumps(creds),headers=headers,verify=False,proxies=self.proxies)
            if sr.status_code != 201:
                print("There was an issue creating the session on target",url+sessionTarget)
                print(sr.content)
                return None
            else:
                data = sr.json()
                headdata = sr.headers
                token = headdata['X-Auth-Token']
                sessionLocation = headdata['Location']
                self.authCookie = token
                self.sessionLocation = sessionLocation
    def endSession(self):
        url = 'https://'+self.mgtInterface+self.sessionLocation
        headers={'content-type': 'application/json','X-Auth-Token': self.authCookie}
        r = requests.delete(url=url,headers=headers,verify=False,proxies=self.proxies)

    def setTargetJSONInfo(self,target,jsonInfo):
        pass

    def extract_power_data(self):
        pf = float(1)
        self.json_object = self.data['power']
        voltage_a = voltage_b = current_a = current_b = 0
        for voltage_target in self.json_object['Voltages']:
            if 'Volt PSU A AC'.lower() in str(voltage_target['Name']).lower():
                #print("seeing voltage A, its",voltage_target['ReadingVolts'] )
                voltage_a = float(voltage_target['ReadingVolts'])
            elif 'Volt PSU B AC'.lower() in str(voltage_target['Name']).lower():
                voltage_b = float(voltage_target['ReadingVolts'])
        for current_target in self.json_object['Oem']['WDC']['Currents']:
            if 'CURR PSU A IN' in current_target['Name']:
                current_a = float(current_target['ReadingAmps'])
            elif 'CURR PSU B IN' in current_target['Name']:
                current_b = float(current_target['ReadingAmps'])
        print("The voltage of PSU A is", voltage_a, " and PSU B is ", voltage_b)
        print("The current of PSU A is", current_a, " and PSU B is", current_b)
        power_a = voltage_a*current_a*pf
        power_b = voltage_b*current_b*pf
        print("Power of PSU A is ",power_a,"Watts Power of PSU B is",power_b,"Watts")
        self.upload_data['Voltage_PSU_A'] = voltage_a
        self.upload_data['Voltage_PSU_B'] = voltage_b
        self.upload_data['Current_PSU_A'] = current_a
        self.upload_data['Current_PSU_B'] = current_b
        self.upload_data['Power_PSU_A'] = power_a
        self.upload_data['Power_PSU_B'] = power_b

    def extract_temperature_data(self):
        mytemps = {item['Name']:item['ReadingCelsius'] for item in self.data['thermal']['Temperatures']}
        self.upload_data.update({str(key):float(value) for (key,value) in mytemps.items()})
