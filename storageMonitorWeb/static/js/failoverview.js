//      <li><span class="caret">Beverages</span>

class physicalErrorOverview{
    constructor(data) {
        console.log("constructor");
        this.data = data; //   {servername:{'attributes':{server attributes},'jbods':{'jbodserial':{'attributes':{jbod attributes},'disks':{diskserialnumber:{disk attributes}}}}
        this.physicalroot = document.createElement("ul");
        this.physicalroot.id = "physicalroot";
        // this.physicalroot.innerHTML = 'Physical View: Servers-JBODs-Hard Drives';
        document.getElementById("div-physicalroot").appendChild(this.physicalroot);
        for(let server in this.data){
            let serverli = document.createElement("li");
            if (this.data[server]['attributes']['nestederror']){
                serverli.className = "nestederror"
            } else if (this.data[server]['attributes']['directerror']) {
                serverli.className = "directerror"
            }else {
                serverli.className = "noerror"
            }
            
        
            serverli.addEventListener("click",displayExpandedInformation)
            serverli.id = 'id_li_'+server;
            let serverspan = document.createElement("span");
            serverspan.id = 'id_s_'+server
            let serverdisplayname = this.data[server]['attributes']['displayname']
            serverspan.className = "caret";
            serverspan.innerHTML = `<img data-devid=${server} data-devtype='headnodes' src='/static/images/bladeserverFront.gif' style='width: 120px; pointer-events: all;' alt="Picture of a Server"> ${serverdisplayname}`;
            serverli.appendChild(serverspan);
            this.physicalroot.appendChild(serverli);
            let serverUL = document.createElement("ul");
            serverUL.id = 'id_ul_'+server;
            serverUL.className = "nested";
            serverli.appendChild(serverUL);

           for(let jbod in this.data[server]['jbods']){
               let jbodli = document.createElement("li");
               if (this.data[server]['jbods'][jbod]['attributes']['nestederror']){
                    jbodli.className = "nestederror"
                } else if (this.data[server]['jbods'][jbod]['attributes']['directerror']) {
                    jbodli.className = "directerror"
                }else {
                    jbodli.className = "noerror"
                }
               jbodli.addEventListener("click",displayExpandedInformation)
               jbodli.id = 'id_li_'+jbod;
               serverUL.appendChild(jbodli);
               let jbodspan = document.createElement("span");
               jbodspan.id = 'id_s_'+jbod
               jbodspan.className = "caret";
               let jboddisplayname = this.data[server]['jbods'][jbod]['attributes']['displayname']
               jbodspan.innerHTML =  `<img data-devid=${jbod} data-devtype='jbods' src='/static/images/ultrastar102.png' style='width: 120px; pointer-events: all;' alt="Picture of a JBOD"> ${jboddisplayname}`;
               jbodli.appendChild(jbodspan);
               let jbodUL = document.createElement("ul");
               jbodUL.id = 'id_ul_'+jbod;
               jbodUL.className = "nested";
               jbodli.appendChild(jbodUL);

               for(let disk in this.data[server]['jbods'][jbod]['disks']){
                   let newdisk = document.createElement("li");
                   if (this.data[server]['jbods'][jbod]['disks'][disk]['attributes']['nestederror']){
                       newdisk.className = "nestederror"
                    } else if (this.data[server]['jbods'][jbod]['disks'][disk]['attributes']['directerror']) {
                        newdisk.className = "directerror"
                    }else {
                        newdisk.className = "noerror"
                    }
                   newdisk.addEventListener("click",displayExpandedInformation)
                   newdisk.id = 'id_'+server+'_'+jbod+'_'+disk;
                   let hddisplayname = this.data[server]['jbods'][jbod]['disks'][disk]['attributes']['displayname']
                   newdisk.innerHTML = `<img data-devid=${disk} data-devtype='harddrives' src='/static/images/12tbwdsasdrive.gif' style='width: 25px; pointer-events: all;' alt="Picture of 12 Tb hard drive."> ${hddisplayname}`;
                   jbodUL.appendChild(newdisk)
               }
           }
        }
    }

}

function displayExpandedInformation(clickedElement){
    console.log("entering display expanded information")
    console.log(clickedElement)
    console.log(typeof(clickedElement))
    console.log(clickedElement.target)
    console.log(typeof(clickedElement.target))
    let devtype = clickedElement.target.dataset['devtype'];
    let devid = clickedElement.target.dataset['devid'];
    let elemid = clickedElement.target.id
    let detailfocus = {'devtype':devtype,'devid':devid,'elemid':elemid}
    console.log("Contents of detail focus")
    console.log(detailfocus)
    updateFailurePage(detailfocus)
    console.log(detailfocus)
    console.log("leaving display expanded information.")

}

function serverSortCallback(obj1,obj2){
    if (obj1['attributes']['displayname'] > obj2['attributes']['displayname']){
        return obj1;
    } else {
        return obj2;
    }
}