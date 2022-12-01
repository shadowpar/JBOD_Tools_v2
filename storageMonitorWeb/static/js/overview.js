//      <li><span class="caret">Beverages</span>

class physicalOverview{
    constructor(data) {
        console.log("constructor");
        this.data = data; //   {servername:{'attributes':{server attributes},'jbods':{'jbodserial':{'attributes':{jbod attributes},'disks':{diskserialnumber:{disk attributes}}}}
        for(let item in this.data){
            console.log(item)
            // console.log(this.data[item])
        }
        this.physicalroot = document.createElement("ul");
        this.physicalroot.id = "physicalroot";
        this.physicalroot.innerHTML = 'Physical View: Servers-JBODs-Hard Drives';
        document.getElementById("div-physicalroot").appendChild(this.physicalroot);

        for(let server in this.data){
            let serverli = document.createElement("li");
            serverli.id = 'id_li_'+server;
            let serverspan = document.createElement("span");
            serverspan.id = 'id_s_'+server
            serverspan.className = "caret";
            serverspan.innerHTML = `<img src='/static/images/bladeserverFront.gif' style='width: 120px' alt="Picture of a Server"> ${server}`;
            serverli.appendChild(serverspan);
            this.physicalroot.appendChild(serverli);
            let serverUL = document.createElement("ul");
            serverUL.id = 'id_ul_'+server;
            serverUL.className = "nested";
            serverli.appendChild(serverUL);

           for(let jbod in this.data[server]['jbods']){
               let jbodli = document.createElement("li");
               jbodli.id = 'id_li_'+jbod;
               serverUL.appendChild(jbodli);
               let jbodspan = document.createElement("span");
               jbodspan.id = 'id_s_'+jbod
               jbodspan.className = "caret";
               // jbodspan.innerText = this.data[server]['jbods'][jbod]['attributes']['name']
               jbodspan.innerHTML = `<button form="jbodform" type="submit" name="targetJBOD" value="${jbod}"><img src='/static/images/ultrastar102.png' style='width: 120px' alt="Picture of a Server"></button> ${this.data[server]['jbods'][jbod]['attributes']['logicalid']}`;
               jbodli.appendChild(jbodspan);
               let jbodUL = document.createElement("ul");
               jbodUL.id = 'id_ul_'+jbod;
               jbodUL.className = "nested";
               jbodli.appendChild(jbodUL);

               for(let disk in this.data[server]['jbods'][jbod]['disks']){
                   let newdisk = document.createElement("li");
                   newdisk.id = 'id_'+server+'_'+jbod+'_'+disk;
                   // newdisk.innerText = 'Hard drive in slot '+disk
                   newdisk.innerHTML = `<img src='/static/images/12tbwdsasdrive.gif' style='width: 25px' alt="Picture of 12 Tb hard drive."> ${'Index '+disk}`;
                   jbodUL.appendChild(newdisk)
               }
           }
        }
    }

}

