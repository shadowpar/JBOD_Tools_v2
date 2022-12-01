from hancockStorageMonitor.database.db_manager import db_manager
# from hancockStatusMonitor.database import jbod, harddrive, logicaldisk, raidarray
from hancockStorageMonitor.database.sqlalchemy_classes import jbod,raidarray,harddrive

class displayJBOD(object):
    def __init__(self,jbodserial):
        self.dbmanager = db_manager()
        self.attributes = {'serialnumber':jbodserial}
        self.disks = {}
        self.raidarrayIDmap = {}
        self.getInfoFromDB()

    def getInfoFromDB(self):
        jbodObj = self.dbmanager.session.query(jbod).filter(jbod.serialnumber == self.attributes['serialnumber']).first()
        print(type(jbodObj))
        self.attributes['id'] = jbodObj.id
        self.attributes['numslots'] = jbodObj.numslots
        self.attributes['displayClass'] = "ultrastar101"
        self.attributes['headnodeid'] = jbodObj.headnode
        raidarrayObjs = self.dbmanager.session.query(raidarray).filter(raidarray.headnode == self.attributes['headnodeid'])
        if raidarrayObjs is not None:
            for arrayObj in raidarrayObjs:
                self.raidarrayIDmap[arrayObj.id] = arrayObj.name


        diskObjs = self.dbmanager.session.query(harddrive).filter(harddrive.jbod == self.attributes['id'])
        if diskObjs.count() != jbodObj.numslots:
            print("Some disks appear to be missing from the database or this JBOD is not fully populated.")
        for item in diskObjs:
            self.disks[item.index] = item.returnImportantProperties()
            if item.raidarray in self.raidarrayIDmap:
                self.disks[item.index]['raidarray'] = self.raidarrayIDmap[item.raidarray]
            else:
                self.disks[item.index]['raidarray'] = 'Not in RAID array.'
