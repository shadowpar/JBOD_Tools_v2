# hancockStorageMonitor

    This consists of two main executables and library. One executable called storageCentralScan.py is run on a central
server that can access all storage servers via ssh. This program pulls JSON data from each host. That data is processed
and written to a database. If the database does not exist, it will be created according to the sqlalchemy ORM definitions
in the library.
    The second main executable storageServerScan.py runs as a cron job on each storage host. It gathers a variety of data from the host and
writes that data to a JSON file, /tmp/$hostnamename_storageMonitor.dat by default. This is the file retrieved by the
central storage executable.