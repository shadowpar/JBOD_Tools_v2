from os import system
from time import sleep
from collections import OrderedDict
from hancockStorageMonitor.colorama import Fore, Style, Back
from contextlib import redirect_stdout
from hancockStorageMonitor.common.staticdatastorage import VALIDDISKCOUNTS
from pprint import pprint

class selectmenu(object):
    def __init__(self,menuitems={}, title='Generic Selection Menu',pretext='',autosort=True):
        self.title = title
        self.pretext = pretext
        self.menuitems = menuitems
        self.data = {}
        if type(self.menuitems) ==  OrderedDict:
            self.autosort = False
        else:
            self.autosort = autosort
        self.menuchoices = list(self.menuitems.keys())
        if autosort:
            self.menuchoices.sort()
        self.retstring = 'Close this menu.'
        self.menuitems[self.retstring] = None
        self.menuchoices.append(self.retstring)

    def addmenuitem(self,key,value,data={}):
        print("Passed into menuitem with key",key," with title",self.title)
        print(data.keys())
        self.menuchoices.pop(-1)
        self.menuitems[key] = value
        if len(data) == 0:
            self.data[key] = key
        else:
            self.data[key] = data
        self.menuchoices.append(key)
        if self.autosort:
            self.menuchoices.sort()
        self.menuchoices.append(self.retstring)

    def removemenuitem(self,key):
        if key in self.menuitems:
            del self.menuitems[key]
        if key in self.menuchoices:
            self.menuchoices.pop(key)

    def displaymenu(self):
        while True:
            input("press any key to continue")
            system("clear")
            print("\n\n\n\n\n\n",self.title,"\n\n",self.pretext,"\n\n")
            self.pretext = ''
            for choice in self.menuchoices:
                print(f"{self.menuchoices.index(choice)}: {choice}")
            try:
                userpick = int(input("\nPlease select from the available choices above. Select using the numbers only.\n"))
                choice = self.menuchoices[userpick]
                menuvalue = self.menuitems[choice]
                #  If the value of a menuitem is a function, then pass the key of the menu item to that function.
                if callable(menuvalue):
                    if type(self.data[choice]) == dict:
                        print("stop 1")
                        print(choice)
                        print(menuvalue)
                        print(self.data[choice].keys())
                        input("press a key")
                        menuvalue(**self.data[choice])
                    else:
                        print("stop 2")
                        print(choice)
                        print(menuvalue)
                        print(self.data[choice])
                        input("press a key")
                        menuvalue(choice)
                else:
                    #  If the value of a menu item is not a function, that just return to the selected value.

                    return menuvalue
            except ValueError:
                self.pretext = Fore.RED+"That is not a valid choice. Please try again.\n"+Style.RESET_ALL
            except IndexError:
                self.pretext = Fore.RED+"That is not a valid choice. Please try again.\n"+Style.RESET_ALL
            except Exception as e:
                self.pretext = str(e)+Fore.RED+"\nThat is not a valid choice. Please try again.\n"+Style.RESET_ALL

class displayRow(object):
    def __init__(self,rowlabel='rowlabel'):
        self.rowlabel = rowlabel
        self.cells = []
        self.cellwidths = []

    def addcell(self,contents='cellcontents',position=None):
        if position is None:
            self.cells.append(contents)
            self.cellwidths.append(len(contents))
        else:
            while position > len(self.cells):
                self.addcell()
            self.cells[position] = contents
            self.cellwidths[position] = len(contents)
    def genPrintLine(self,colwidths=None,lpad=1,rpad=1,prepend='|',postpend='|',highlights={},normalcolor="RESET"):
        for item in highlights:
            if highlights[item].upper() not in Fore.__dict__:
                print("All color parameters must be one of the following choices. Using defaults instead. Not valid:"+str(highlights[item]))
                print(list(Fore.__dict__.keys()))
                highlights[item] = "RESET"
        if normalcolor.upper() not in Fore.__dict__:
            print("All color parameters must be one of the following choices. Using defaults instead. Not valid:"+str(normalcolor))
            normalcolor = "RESET"

        if colwidths is None:
            colwidths = [len(prepend)+lpad+len(cell)+rpad+len(postpend) for cell in self.cells]
        line = ''
        for i in range(len(self.cells)):
            line = line + prepend+self.cells[i].center(colwidths[i]-len(prepend))
        line = line + postpend
        linecolor = getattr(Fore,normalcolor)
        for item in highlights:
            if item in line:
                linecolor = getattr(Fore,highlights[item])
        line = linecolor + line + Fore.RESET
        return line


class displayTable(object):
    def __init__(self,header='Generic Table Header'):
        self.header = header
        self.columnlabels = []
        self.columnwidths = []
        self.rows = []
        self.rowlabelwidth = 0

    def addrow(self,rowobject=displayRow(),position=None):
        while len(rowobject.cells) > len(self.columnlabels):
            self.setColumnLabel(position=len(self.columnlabels))
        if len(rowobject.rowlabel) > self.rowlabelwidth:
            self.rowlabelwidth = len(rowobject.rowlabel)
        for index in range(len(rowobject.cellwidths)):
            if rowobject.cellwidths[index] > self.columnwidths[index]:
                self.columnwidths[index] = rowobject.cellwidths[index]

        if position is None:
            self.rows.append(rowobject)
        else:
            while position > len(self.rows):
                self.addrow()
            self.rows.insert(position,rowobject)

    def setColumnLabel(self,position=None,columnlabel='columnlabel'):
        if position is None:
            self.columnlabels.append(columnlabel)
            self.columnwidths.append(len(columnlabel))
            return
        try:
            self.columnlabels[position] = columnlabel
        except IndexError:
            while len(self.columnlabels) <= position:
                self.columnlabels.append('columnlabel')
            self.columnlabels[position] = columnlabel
        try:
            self.columnwidths[position] = len(columnlabel)
        except IndexError:
            while len(self.columnwidths) <= position:
                self.columnwidths.append(len(columnlabel))
            self.columnwidths[position] = len(columnlabel)

    def printtable(self, lpad=1, rpad=1, vsep='|', hsep='-',colors={},highlights={}):
        defaultColors = {'sep':"BLUE",'clabel':"WHITE",'normal':"GREEN",'header':"BLUE"}
        for item in colors:
            if colors[item].upper() not in Fore.__dict__:
                print("All color parameters must be one of the following choices. Using defaults instead. Not valid:" + str(colors[item]))
                colors[item] = "RESET"
        for item in defaultColors:
            if item not in colors:
                colors[item] = defaultColors[item]
        self.colors = colors
        collabelrow = displayRow(rowlabel='')
        for label in self.columnlabels:
            collabelrow.addcell(contents=label)
        colWidthsWithSpacers = [len(vsep) + lpad + item + rpad + len(vsep) for item in self.columnwidths]
        totalwidth = sum(colWidthsWithSpacers)
        plines = [collabelrow.genPrintLine(colwidths=colWidthsWithSpacers, lpad=lpad, rpad=rpad, prepend=vsep, postpend=vsep)]
        print("\n")
        print(getattr(Fore,colors['header']) +self.header.center(totalwidth)+Style.RESET_ALL)
        print("\n")
        for item in self.rows:
            newline = item.genPrintLine(colwidths=colWidthsWithSpacers, lpad=lpad, rpad=rpad, prepend=vsep, postpend=vsep,normalcolor=self.colors['normal'],
                                        highlights=highlights)
            plines.append(newline)
        sepline = getattr(Fore,self.colors['sep'])+hsep*totalwidth+Fore.RESET
        print(sepline)
        for line in plines:
            print(line)
            print(sepline)

class superDisplayTable(object):
    def __init__(self,header='Generic Super Table Header'):
        # A mapping from table position to displayTable object.
        self.tables = {}

    def addTable(self,table,position=None):
        #  Position is (x,y) coordinate for table placement.
        if position is None:
            position = self.getNextPosition()

    def getNextPosition(self):
        # A function to decide next available table position within supertable
        return (1,1)
    def printsupertable(self):
        pass

def showdisks(info=None,colors={},highlights={}):
    #  Color keys can include 'sep' for seperator color, 'normal' for normal line color, 'header' for table header color
    #  'clabel' for column label color. Highlights contains a mapping between strings whos rows should be highlighted mapped
    #  to the colors that is should be highlighted. For instance {'Error':"RED"}

    if 'header' not in colors or colors['header'].upper() not in Fore.__dict__:
        colors['header'] = "RESET"
    translate = {'Index':'index','Slot':'slot','Disk Name':'name','Multipath Device':'mpathdev','RAID Partition':'raidpartition',
                   'RAID':'mdparent','SAS Address':'sasaddress','LED ON':'indicatorled'}
    hddata = ['index','slot','mpathdev','mpathdevfriendly','raidpartition','raidpartitionfriendly','indicatorled','mdparent']
    lddata = ['name','sasaddress']
    if info is None:
        print("This class requires an instance of info=storage_info() class.")
        return None
    with redirect_stdout(open('/dev/null', 'w')):
        xdata = info.exportDictionary()
    pdata = {}
    for ld in xdata['logicaldisks']:
        cserial = xdata['logicaldisks'][ld]['chassisSerial']
        encl = xdata['logicaldisks'][ld]['enclosure']
        if cserial not in pdata:
            pdata[cserial] = {}
        if encl not in pdata[cserial]:
            pdata[cserial][encl] = {}
        serial = xdata['logicaldisks'][ld]['serialnumber']
        index = int(xdata['harddrives'][serial]['index'])
        pdata[cserial][encl][index] = {}
        for item in hddata:
            try:
                pdata[cserial][encl][index][item] = xdata['harddrives'][serial][item]
            except KeyError:
                pdata[cserial][encl][index][item] = 'error'
        # Change mdparent UUID into a human readable name.
        mdparent = pdata[cserial][encl][index]['mdparent']
        try:
            pdata[cserial][encl][index]['mdparent'] = xdata['raidarrays'][mdparent]['name']
        except KeyError:
            pass
        for item in lddata:
            try:
                pdata[cserial][encl][index][item] = xdata['logicaldisks'][ld][item]
            except KeyError:
                pdata[cserial][encl][index][item] = 'error'
    tables = []
    for jb in pdata:
        print(getattr(Fore,colors['header']))
        logicalid = Style.BRIGHT+xdata['jbods'][jb]['logicalid']+Style.NORMAL
        print("\n\nEnclosures inside JBOD chassis with serial number: " + Style.BRIGHT+jb+Style.NORMAL + " and logicalid: " + logicalid)
        print(Style.RESET_ALL)
        for encl in pdata[jb]:
            #  Create table for each enclosure
            dtable = displayTable(header='Start of logical disks in enclosure '+Style.BRIGHT+encl+Style.NORMAL)
            if len(pdata[jb][encl]) < int(xdata['jbods'][jb]['numslots']):
                allindexes = set([item for item in range(int(xdata['jbods'][jb]['numslots']))])
                missingIndexes = allindexes.difference(set(list(pdata[jb][encl].keys())))
                for index in missingIndexes:
                    pdata[jb][encl][int(index)] = {item:'missing' for item in hddata}
                    pdata[jb][encl][int(index)].update({item:'missing' for item in lddata})
                    pdata[jb][encl][int(index)]['index'] = index
            pdata[jb][encl] = OrderedDict(sorted(pdata[jb][encl].items()))

            for item in translate:
                dtable.setColumnLabel(columnlabel=item)
            for index in pdata[jb][encl]:
                row = displayRow(rowlabel='')
                for item in translate:
                    if translate[item] == 'mpathdev':
                        c1 = str(pdata[jb][encl][index][translate[item]])
                        try:
                            c2 = str(pdata[jb][encl][index]['mpathdevfriendly'])
                        except KeyError:
                            c2 = 'missing'
                        contents = c1+' / '+c2
                    elif translate[item] == 'raidpartition':
                        c1 = str(pdata[jb][encl][index][translate[item]])
                        try:
                            c2 = str(pdata[jb][encl][index]['raidpartitionfriendly'])
                        except KeyError:
                            c2 = 'missing'
                        contents = c1+' / '+c2
                    else:
                        contents = str(pdata[jb][encl][index][translate[item]])
                    row.addcell(contents=contents)
                dtable.addrow(rowobject=row)
            tables.append(dtable)
            dtable.printtable(colors=colors,highlights=highlights)
    return tables