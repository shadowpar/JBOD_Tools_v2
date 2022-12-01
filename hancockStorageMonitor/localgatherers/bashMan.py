from pprint import pprint
import subprocess
from time import sleep

class bashman(object):
    def __init__(self):
        super(bashman, self).__init__()
        proc = subprocess.Popen(['/bin/bash'],stderr=subprocess.PIPE,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
        while True:
            command = input("Type your command.\n")+"\n"
            command = command.encode()
            print("The contents of proc.poll is",str(proc.poll()))
            comms = proc.communicate(input=command,)
            stdout_data = comms[0].decode()
            stderr_data = comms[1].decode()
            print(stdout_data,stderr_data)
            print("return code is ",proc.returncode)
            print("The PID is :",proc.pid)
            print("The contents of proc.poll is",str(proc.poll()))
            proc.returncode = None

talker = bashman()


