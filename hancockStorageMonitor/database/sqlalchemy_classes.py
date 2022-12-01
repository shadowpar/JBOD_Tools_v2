from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, BigInteger, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import timedelta, datetime
utcoffset = timedelta(hours=-5)

Base = declarative_base()

class storageerror(Base):
    __tablename__ = 'storageerrors'
    id = Column(Integer, primary_key=True)
    errortype = Column('errortype',String(25))
    devtable = Column('devtable',String(15))
    description = Column('description',String(255))
    deviceid = Column('deviceid',Integer,nullable=True)
    deviceunique = Column('deviceunique',String(32),nullable=True)
    modified = Column('modified',DateTime)
    def __init__(self,errorType,devTable,description,deviceid,deviceunique,modified=datetime.utcnow()):
        self.errortype = errorType
        self.devtable = devTable
        self.description = description
        self.deviceid = deviceid
        self.deviceunique = deviceunique #This is usually a human readable name of a device.
        self.modified = modified
    def returnImportantProperties(self):
        properties = {'errortype':self.errortype,'devtable':self.devtable,'description':self.description,
                      'deviceid':self.deviceid,'deviceunique':self.deviceunique,'modified':str(self.modified-utcoffset)}
        return properties


class cpu(Base):
    __tablename__ = 'cpus'
    id = Column(Integer, primary_key=True)
    model = Column('model', String(50),unique=True)
    architecture = Column('architecture',String(10))
    bogomips = Column('bogomips',Float)
    byteorder = Column('byteorder',String(15))
    numcores = Column(Integer)
    cpufreqmhz = Column(Float)
    opmodes = Column('opmodes',String(20))
    l1dcache = Column('l1dcache',String(10))
    l1icache = Column('l1icache',String(10))
    l2cache = Column('l2cache',String(10))
    l3cache = Column('l3cache',String(10))
    threadspercore = Column(Integer)
    vendor = Column('vendor',String(32))
    virtualization = Column('virtualization',String(20))
    modified = Column('modified',DateTime)

    def __init__(self,model=None,architecture='error',bogomips=-1,byteorder='error',numcores=-1,cpufreqmhz=-1,opmodes='error',l1dcache='error',l1icache='error',l2cache='error',l3cache='error',threadspercore=-1,vendor='error',virtualization='error',modified=datetime.utcnow()):
        self.model = model
        self.architecture = architecture
        self.bogomips = bogomips
        self.byteorder = byteorder
        self.numcores = numcores
        self.cpufreqmhz = cpufreqmhz
        self.opmodes = opmodes
        self.l1dcache = l1dcache
        self.l1icache = l1icache
        self.l2cache =l2cache
        self.l3cache = l3cache
        self.threadspercore = threadspercore
        self.vendor = vendor
        self.virtualization = virtualization
        self.modified = modified

    def returnImportantProperties(self):
        properties = {'model':self.model,'architecture':self.architecture,'bogomips':self.bogomips,'byteorder':self.byteorder,'numcores':self.numcores,'cpufreqmhz':self.cpufreqmhz,'opmodes':self.opmodes,'l1dcache':self.l1dcache,'l1icache':self.l1icache,
                      'l2cache':self.l2cache,'l3cache':self.l3cache,'threadspercore':self.threadspercore,'vendor':self.vendor,'virtualization':self.virtualization,'modified':str(self.modified-utcoffset)}
        return properties

class headnode(Base):
    __tablename__ = 'headnodes'
    id = Column(Integer, primary_key=True)
    name = Column('name',String(32),unique=True)
    cpu = Column(Integer)
    model = Column('model',String(32))
    datacenter = Column('datacenter',String(32))
    rack = Column('rack',String(5))
    slot = Column('slot', Integer)
    experiment = Column('experiment',String(32))
    numsockets = Column(Integer)
    numtotalthreads = Column(Integer)
    raidtype = Column('raidtype',String(10),nullable=True)
    serialnumber = Column(String(25),nullable=True)
    modified = Column('modified',DateTime)
    jbods = relationship("jbod")
    raidarrays = relationship("raidarray")
    harddrives = relationship("harddrive")
    def __init__(self,name,cpu=-1,model='error',datacenter='error',rack='error',slot=-1, experiment='error',numsockets=-1,numtotalthreads=-1,raidtype=None,serialnumber=None, modified=datetime.utcnow()):
        self.name = name
        self.cpu = cpu
        self.model = model
        self.datacenter = datacenter
        self.rack = rack
        self.slot = slot
        self.experiment = experiment
        self.numsockets = numsockets
        self.numtotalthreads = numtotalthreads
        self.raidtype = raidtype
        self.serialnumber = serialnumber
        self.modified = modified
    def returnImportantProperties(self):
        properties = {'name':self.name,'cpu':self.cpu,'model':self.model,'datacenter':self.datacenter,'rack':self.rack,'experiment':self.experiment,'numsockets':self.numsockets,
        'numtotalthreads':self.numtotalthreads,'raidtype':self.raidtype,'serialnumber':self.serialnumber,'modified':str(self.modified-utcoffset)}
        return properties

class jbod(Base):
    __tablename__ = 'jbods'
    id = Column(Integer, primary_key=True)
    headnode = Column(Integer, ForeignKey('headnodes.id'))
    vendor = Column('vendor',String(32))
    model = Column('model',String(32))
    serialnumber = Column('serialnumber',String(32),unique=True,nullable=False)
    health = Column('health',String(32))
    datacenter = Column('datacenter', String(32))
    rack = Column('rack',String(5))
    slot = Column('slot',Integer)
    numslots = Column('numslots',Integer)
    logicalid = Column('logicalid',String(32))
    managementmaca = Column('managementmaca',String(17))
    managementstatusa = Column('managementlinkstatusa',String(32))
    managementipa = Column('managementipa',String(16))
    managementmacb = Column('managementmacb', String(17))
    managementstatusb = Column('managementlinkstatusb',String(32))
    managementipb = Column('managementipb',String(16))
    modified = Column('modified',DateTime)
    def __init__(self, headnode, vendor='', model='', serialnumber='', health='unknown', datacenter='', rack='', slot=0, numslots=0, logicalid='',
                 managementipa='',managementstatusa='',managementmaca='', managementipb='',managementstatusb='',managementmacb='',modified=datetime.utcnow()):
        self.model = model
        self.serialnumber = serialnumber
        self.headnode = headnode
        self.vendor = vendor
        self.datacenter = datacenter
        self.health = health
        self.rack = rack
        self.slot = slot
        self.numslots = numslots
        self.logicalid = logicalid
        self.managementmaca = managementmaca
        self.managementipa = managementipa
        self.managementstatusa = managementstatusa
        self.managementmacb = managementmacb
        self.managementipb = managementipb
        self.managementstatusb = managementstatusb
        self.modified = modified

    def returnImportantProperties(self):
        properties = {'model':self.model,'serialnumber':self.serialnumber,'headnode':self.headnode,
                      'vendor':self.vendor,'datacenter':self.datacenter,'health':self.health,'rack':self.rack,'slot':self.slot,
                      'numslots':self.numslots,'logicalid':self.logicalid,'managementmaca':self.managementmaca,'managementipa':self.managementipa,
                    'managementstatusa':self.managementstatusa,'managementmacb':self.managementmacb,'managementipb':self.managementipb,
                      'managementstatusb':self.managementstatusb,'modified':str(self.modified-utcoffset)}
        return properties

class raidarray(Base):
    __tablename__ = 'raidarrays'
    id = Column(Integer, primary_key=True)
    headnode = Column(Integer, ForeignKey('headnodes.id'))
    name = Column('name',String(32))
    uuid = Column('uuid',String(40),unique=True)
    chunksize = Column(Integer)
    componentsize = Column(BigInteger)
    degraded = Column('degraded',Boolean)
    totalnumdisks = Column(Integer)
    lastsyncaction = Column('lastsyncaction',String(32))
    mismatchcnt = Column('mismatchcnt',String(32))
    syncspeed = Column('syncspeed',String(32))
    syncspeedmax = Column('syncspeedmax',String(32))
    syncspeedmin = Column('syncspeedmin',String(32))
    syncaction = Column('syncaction',String(32))
    stripecachesize = Column('stripecachesize',String(32))
    raidlevel = Column('raidlevel',String(20))
    consistencypolicy = Column('consistencypolicy',String(32))
    arraystate = Column('arraystate',String(32))
    metadataversion = Column('metadataversion',String(20))
    major = Column('major',String(5))
    minor = Column('minor',String(5))
    mountpoint = Column('mountpoint',String(32))
    filesystem = Column('filesystem',String(10))
    bitmapfile = Column('bitmapfile',String(32))
    modified = Column('modified',DateTime)

    def __init__(self,headnode,name,uuid,chunksize,componentsize,degraded,totalnumdisks,lastsyncaction,mismatchcnt,
                 syncspeed,syncspeedmax,syncspeedmin,syncaction,stripecachesize,raidlevel,consistencypolicy,
                 arraystate,metadataversion,major,minor,mountpoint,filesystem,bitmapfile,modified):
        self.name = name
        self.headnode = headnode
        self.uuid = uuid
        self.chunksize = chunksize
        self.componentsize = componentsize
        self.degraded = degraded
        self.totalnumdisks = totalnumdisks
        self.lastsyncaction = lastsyncaction
        self.mismatchcnt = mismatchcnt
        self.syncspeed = syncspeed
        self.syncspeedmax = syncspeedmax
        self.syncspeedmin = syncspeedmin
        self.syncaction = syncaction
        self.stripecachesize = stripecachesize
        self.raidlevel = raidlevel
        self.consistencypolicy = consistencypolicy
        self.arraystate = arraystate
        self.metadataversion = metadataversion
        self.major = major
        self.minor = minor
        self.mountpoint = mountpoint
        self.filesystem = filesystem
        self.bitmapfile = bitmapfile
        self.modified = modified

    def returnImportantProperties(self):
        properties = {'headnode':self.headnode,'name':self.name,'uuid':self.uuid,'chunksize':self.chunksize,
                      'componentsize':self.componentsize,'degraded':self.degraded,'totalnumdisks':self.totalnumdisks,
                      'lastsyncaction':self.lastsyncaction,'mismatchcnt':self.mismatchcnt,'syncspeed':self.syncspeed,
                      'syncspeedmax':self.syncspeedmax,'syncspeedmin':self.syncspeedmin,'syncaction':self.syncaction,
                      'stripecachesize':self.stripecachesize,'raidlevel':self.raidlevel,
                      'consistencypolicy':self.consistencypolicy,'arraystate':self.arraystate,
                      'metadataversion':self.metadataversion,'major':self.major,'minor':self.minor,
                      'mountpoint':self.mountpoint,'filesystem':self.filesystem,'bitmapfile':self.bitmapfile,
                      'modified':str(self.modified)}
        return properties

class harddrive(Base):
    __tablename__ = 'harddrives'
    id = Column(Integer, primary_key=True)
    headnode = Column(Integer, ForeignKey('headnodes.id'))
    raidarray = Column(Integer,nullable=True)
    jbod = Column(Integer, ForeignKey('jbods.id'))
    vendor = Column('vendor',String(32))
    model = Column('model',String(32))
    firmware = Column('firmware',String(32))
    serialnumber = Column('serialnumber',String(32),unique=True)
    temperature = Column(Integer)
    smartstatus = Column('smartstatus',String(32))
    growndefects = Column(Integer)
    
    readerrorcorrectedtotal = Column(BigInteger)
    readerroruncorrectedtotal = Column(BigInteger)
    readerrorcorrectedbyreadwrite = Column(BigInteger)
    readerrorcorrectedeccfast = Column(BigInteger)
    readerrorcorrectedeccdelayed = Column(BigInteger)
    verifyerrorcorrectedtotal = Column(BigInteger)
    verifyerroruncorrectedtotal = Column(BigInteger)
    verifyerrorcorrectedbyreadwrite = Column(BigInteger)
    verifyerrorcorrectedeccfast = Column(BigInteger)
    verifyerrorcorrectedeccdelayed = Column(BigInteger)
    writeerrorcorrectedtotal = Column(BigInteger)
    writeerroruncorrectedtotal = Column(BigInteger)
    writeerrorcorrectedbyreadwrite = Column(BigInteger)
    writeerrorcorrectedeccfast = Column(BigInteger)
    writeerrorcorrectedeccdelayed = Column(BigInteger)
    rotationrate = Column(Integer)
    capacity = Column(BigInteger)
    protocol = Column('protocol',String(10))
    health = Column('health',String(32))
    indicatorled = Column(Boolean)
    index = Column(Integer)
    slot = Column(Integer)
    modified = Column('modified',DateTime)
    def __init__(self,headnode,serialnumber, index=0,slot=1, jbod=None,raidarray=None,vendor='',model='',firmware='',temperature=0,smartstatus='',
                 growndefects=0,rotationrate=0,capacity=0,protocol='',health='',indicatorled=False, readerrorcorrectedtotal=0, readerroruncorrectedtotal=0,
                 readerrorcorrectedbyreadwrite=0,readerrorcorrectedeccfast=0,readerrorcorrectedeccdelayed=0,
                 verifyerrorcorrectedtotal=0, verifyerroruncorrectedtotal=0, verifyerrorcorrectedbyreadwrite=0, verifyerrorcorrectedeccfast=0, verifyerrorcorrectedeccdelayed=0,
                 writeerrorcorrectedtotal=0, writeerroruncorrectedtotal=0, writeerrorcorrectedbyreadwrite=0, writeerrorcorrectedeccfast=0, writeerrorcorrectedeccdelayed=0,
                 modified=datetime.utcnow()):
        self.headnode = headnode
        self.serialnumber = serialnumber
        self.jbod = jbod
        self.raidarray = raidarray
        self.vendor = vendor
        self.model = model
        self.firmware = firmware
        self.temperature = temperature
        self.smartstatus = smartstatus
        self.growndefects = growndefects
        self.readerrorcorrectedtotal = readerrorcorrectedtotal
        self.readerroruncorrectedtotal = readerroruncorrectedtotal
        self.readerrorcorrectedbyreadwrite = readerrorcorrectedbyreadwrite
        self.readerrorcorrectedeccfast = readerrorcorrectedeccfast
        self.readerrorcorrectedeccdelayed = readerrorcorrectedeccdelayed
        self.verifyerrorcorrectedtotal = verifyerrorcorrectedtotal
        self.verifyerroruncorrectedtotal = verifyerroruncorrectedtotal
        self.verifyerrorcorrectedbyreadwrite = verifyerrorcorrectedbyreadwrite
        self.verifyerrorcorrectedeccfast = verifyerrorcorrectedeccfast
        self.verifyerrorcorrectedeccdelayed = verifyerrorcorrectedeccdelayed
        self.writeerrorcorrectedtotal = writeerrorcorrectedtotal
        self.writeerroruncorrectedtotal = writeerroruncorrectedtotal
        self.writeerrorcorrectedbyreadwrite = writeerrorcorrectedbyreadwrite
        self.writeerrorcorrectedeccfast = writeerrorcorrectedeccfast
        self.writeerrorcorrectedeccdelayed = writeerrorcorrectedeccdelayed
        self.rotationrate = rotationrate
        self.capacity = capacity
        self.protocol = protocol
        self.health = health
        self.indicatorled = indicatorled
        self.index = index
        self.slot = slot
        self.modified = modified
    def returnImportantProperties(self):
        properties = {'slot':self.slot, 'serialnumber':self.serialnumber,'smartstatus':self.smartstatus,'index':self.index,'vendor':self.vendor,
                      'model':self.model,'firmware':self.firmware, 'temperature':self.temperature,
                      'growndefects':self.growndefects, 'readerrorcorrectedtotal': self.readerrorcorrectedtotal,
                      'readerroruncorrectedtotal': self.readerroruncorrectedtotal, 'readerrorcorrectedbyreadwrite': self.readerrorcorrectedbyreadwrite,
                      'readerrorcorrectedeccfast': self.readerrorcorrectedeccfast, 'readerrorcorrectedeccdelayed': self.readerrorcorrectedeccdelayed,
                      'verifyerrorcorrectedtotal': self.verifyerrorcorrectedtotal, 'verifyerroruncorrectedtotal': self.verifyerroruncorrectedtotal,
                      'verifyerrorcorrectedbyreadwrite': self.verifyerrorcorrectedbyreadwrite,'verifyerrorcorrectedeccfast': self.verifyerrorcorrectedeccfast,
                      'verifyerrorcorrectedeccdelayed': self.verifyerrorcorrectedeccdelayed, 'writeerrorcorrectedtotal': self.writeerrorcorrectedtotal,
                      'writeerroruncorrectedtotal': self.writeerroruncorrectedtotal,'writeerrorcorrectedbyreadwrite': self.writeerrorcorrectedbyreadwrite,
                      'writeerrorcorrectedeccfast': self.writeerrorcorrectedeccfast,'writeerrorcorrectedeccdelayed': self.writeerrorcorrectedeccdelayed,
                      'rotationrate':self.rotationrate,'capacity':self.capacity,'protocol':self.protocol,
                      'health':self.health,'indicatorled':self.indicatorled,'modified':str(self.modified-utcoffset),'raidarray':self.raidarray}
        return properties

class logicaldisk(Base):
    __tablename__ = 'logicaldisks'
    id = Column(Integer, primary_key=True)
    name = Column('name',String(10))
    harddrive = Column(Integer,ForeignKey('harddrives.id'))
    sasaddress = Column('sasaddress',String(32))
    scsiaddress = Column('scsiaddress',String(16))
    iomodule = Column('iomodule',String(10))
    serialnumber = Column('serialnumber',String(32))
    modified = Column('modified',DateTime)
    def __init__(self,harddrive,name,sasaddress,scsiaddress,serialnumber,iomodule,modified=datetime.utcnow()):
        self.harddrive = harddrive
        self.name = name
        self.serialnumber = serialnumber
        self.sasaddress = sasaddress
        self.scsiaddress = scsiaddress
        self.iomodule = iomodule
        self.modified = modified

    def returnImportantProperties(self):
        properties = {'harddrive':self.harddrive,'name':self.name,'sasaddress':self.sasaddress,'scsiaddress':self.scsiaddress,'iomodule':self.iomodule,'serialnumber':self.serialnumber,'modified':str(self.modified-utcoffset)}
        return properties

# DBSEARCHKEYS = {cpu: 'model', headnode: 'name', jbod: 'serialnumber', harddrive: 'serialnumber', logicaldisk:('serialnumber', 'name'), raidarray: 'uuid'}
# PROCESSINGORDER = OrderedDict({getattr(className, '__tablename__'):className for className in [cpu, headnode, raidarray, jbod, harddrive, logicaldisk]})
# DBREFERENCES = {'logicaldisks':['harddrives'], 'harddrives':['headnodes', 'raidarrays', 'jbods'], 'jbods':['headnodes'], 'raidarrays':['headnodes'], 'headnodes':['cpus'], 'cpus':[]}
# DBDISPLAYNAMES = {'logicaldisks': 'name', 'harddrives': 'serialnumber', 'jbods': 'serialnumber', 'raidarrays': 'name', 'headnodes': 'name', 'cpus': 'model'}