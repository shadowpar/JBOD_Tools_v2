from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from hancockStorageMonitor.database.sqlalchemy_classes import Base

class db_manager(object):
    def __init__(self,dbname='storagedaemon',db_hostname='stmanager-db.sdcc.bnl.gov',db_port=5432):
        self.Base = Base
        self.dbserver = db_hostname
        self.dbname = dbname
        self.dbport = str(db_port)
        self.engine = create_engine('postgresql://postgres:remotePSQL@' + self.dbserver + ':' + self.dbport + '/' + self.dbname)
        Base.metadata.create_all(self.engine)
        self.session_maker = sessionmaker(bind=self.engine)
        self.session = self.session_maker()
