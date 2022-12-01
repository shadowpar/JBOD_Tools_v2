import dbus

#This function uses the systemd DBUS interface to get the PID and statuses of requested service.
def getServiceStatus(serviceName='dbus.service'):
    bus = dbus.SystemBus()
    systemd = bus.get_object('org.freedesktop.systemd1','/org/freedesktop/systemd1')
    #Get the manager interface of systemd dbus implementation.
    manager = dbus.Interface(systemd,'org.freedesktop.systemd1.Manager')
    #Use the manager interface to get the systemd unit corresponding to the serviceName
    try:
        unit = manager.GetUnit(serviceName)
    except dbus.exceptions.DBusException as e:
        print(e)
        print("It appears this is not an active systemd unit.")
        return False, {'procID':None, 'loadState':None, 'activeState':None, 'subState':None}
    #Get a reference to the DBUS object corresponding the systemd unit.
    serviceLeaf = bus.get_object('org.freedesktop.systemd1',unit)
    print(serviceLeaf.object_path)
    #Get a reference to the 'properties' interface of the systemd unit on DBUS.
    PropertiesInterface = dbus.Interface(serviceLeaf,'org.freedesktop.DBus.Properties')
    #Ask the properties interface to get the value of a property (properties exist under each interface), namely  the Process ID of the unit. i.e. /proc/$PID from the "Service" interface of the systemd unit.
    procID = PropertiesInterface.Get('org.freedesktop.systemd1.Service','MainPID')
    loadState = PropertiesInterface.Get('org.freedesktop.systemd1.Unit','LoadState')
    activeState = PropertiesInterface.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
    subState = PropertiesInterface.Get('org.freedesktop.systemd1.Unit', 'SubState')
    info = {'procID':int(procID),'loadState':str(loadState),'activeState':str(activeState),'subState':str(subState)}
    return True, info

#This function uses the dbus interface of redhat entitlement manager to check license status.
#  It will return logical true if there is a valid license, and False if not registered or not redhat.
def checkRedhatEntitlement():
    bus = dbus.SystemBus()
    try:
        redhat = bus.get_object('com.redhat.SubscriptionManager','/EntitlementStatus')
    except dbus.exceptions.DBusException as d:
        print(d)
        print("This is not a redhat system or subscription manager is not installed.")
        return False

    entitlementInterface = dbus.Interface(redhat,'com.redhat.SubscriptionManager.EntitlementStatus')
    result = str(entitlementInterface.check_status())
    values = {'0':True}
    result = values.get(result,False)
    print("The result is ",result,"of type",type(result))
    return result



