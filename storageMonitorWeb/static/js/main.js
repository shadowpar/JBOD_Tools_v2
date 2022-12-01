class ultrastar101 {
  constructor(divElement,attributes,diskattributes) {
    this.id = "mainjbod";
    this.attributes = attributes;
    this.disks = {};
    for(let i=0;i < +this.attributes['numslots'];i++) {
      this.disks[i] = new harddrive(diskattributes[i]);
    }
    this.coords = {'0':"44,68,216,115",'1':"44,118,216,163",'2':"44,165,216,209",'3':"44,211,216,256",'4':"44,258,216,304",'5':"44,305,216,351",'6':"44,352,216,399",
                            '7':"44,445,216,492",'8':"44,492,216,539",'9':"44,540,216,585",'10':"44,587,216,633",'11':"44,634,216,679",'12':"44,682,216,728",'13':"44,729,216,775",
                            '14':"227,68,399,115",'15':"227,118,399,163",'16':"227,165,399,209",'17':"227,211,399,256",'18':"227,258,399,304",'19':"227,305,399,351",'20':"227,352,399,399",
                            '21':"227,445,399,492",'22':"227,492,399,539",'23':"227,540,399,585",'24':"227,587,399,633",'25':"227,634,399,679",'26':"227,682,399,728",'27':"227,729,399,775",
                            '28':"409,68,580,115",'29':"409,118,580,163",'30':"409,165,580,209",'31':"409,211,580,256",'32':"409,258,580,304",'33':"409,305,580,351",'34':"409,352,580,399",
                            '35':"409,445,580,492",'36':"409,492,580,539",'37':"409,540,580,585",'38':"409,587,580,633",'39':"409,634,580,679",'40':"409,682,580,728",'41':"409,729,580,775",
                            '42':"591,68,764,115",'43':"591,118,764,163",'44':"591,165,764,209",'45':"591,211,764,256",'46':"591,258,764,304",'47':"591,305,764,351",
                            '48':"591,492,764,539",'49':"591,540,764,585",'50':"591,587,764,633",'51':"591,634,764,679",'52':"591,682,764,728",'53':"591,729,764,775",
                            '54':"811,92,985,138",'55':"811,141,985,187",'56':"811,188,985,234",'57':"811,236,985,282",'58':"811,282,985,328",'59':"811,329,985,375",
                            '60':"811,468,985,514",'61':"811,516,985,562",'62':"811,563,985,608",'63':"811,611,985,657",'64':"811,658,985,704",'65':"811,705,985,752",
                            '66':"995,92,1166,138",'67':"995,141,1166,187",'68':"995,188,1166,234",'69':"995,236,1166,282",'70':"995,282,1166,328",'71':"995,329,1166,375",
                            '72':"995,468,1166,514",'73':"995,516,1166,562",'74':"995,563,1166,608",'75':"995,611,1166,657",'76':"995,658,1166,704",'77':"995,705,1166,752",
                            '78':"1176,92,1348,138",'79':"1176,141,1348,187",'80':"1176,188,1348,234",'81':"1176,236,1348,282",'82':"1176,282,1348,328",'83':"1176,329,1348,375",
                            '84':"1176,468,1348,514",'85':"1176,516,1348,562",'86':"1176,563,1348,608",'87':"1176,611,1348,657",'88':"1176,658,1348,704",'89':"1176,705,1348,752",
                            '90':"1360,92,1532,138",'91':"1360,141,1532,187",'92':"1360,188,1532,234",'93':"1360,236,1532,282",'94':"1360,282,1532,328",'95':"1360,329,1532,375",
                            '96':"1360,468,1532,514",'97':"1360,516,1532,562",'98':"1360,563,1532,608",'99':"1360,611,1532,657",'100':"1360,658,1532,704",'101':"1360,705,1532,752"};

    this.mainimage =  document.createElement("img");
    this.mainimage.id = "jbodmainimage";
    this.mainimage.src = "/static/images/ultrastar102.png";
    this.mainimage.style.width = "100%"
    this.mainimage.style.zIndex = "1";
    divElement.appendChild(this.mainimage);
    this.makeMap(divElement);
    this.mainimage.useMap = "#workmap";
    this.tooltip = document.createElement("canvas");
    this.tooltip.id = "tooltip";
    document.getElementById("div-tooltip").appendChild(this.tooltip);
    this.tooltip.style.position = "absolute";
    this.tooltip.style.zIndex = "5";
    this.tooltip.style.left = "0px";
    this.tooltip.style.right = "0px";
    this.tooltip.width = this.tooltip.parentElement.clientWidth
    this.tooltip.height = this.tooltip.parentElement.clientHeight
    this.tooltip.style.width = "100%";
    this.tooltip.style.border = "5px solid black"
    this.tooltip.style.backgroundColor = "green";
    this.tooltip.style.visibility = "visible";

    this.highlight = document.createElement("canvas");
    this.highlight.id= "highlight";
    this.highlight.style.position = "absolute";
    this.highlight.style.zIndex = "2";
    this.highlight.width = 160;
    this.highlight.height = 36;
    this.highlight.style.left = "1360px";
    this.highlight.style.top = "705px";
    this.highlight.style.border = "5px solid green";
    this.highlight.style.visibility = "hidden";
    this.highlight.style.pointerEvents = "none";
    this.highlight.setAttribute("alt","notarget");
    divElement.appendChild(this.highlight)

  }

  makeMap(divElement) {
    this.mymap = document.createElement("map");
    this.mymap.id = "workmap";
    this.mymap.name = "workmap";
    for(let item in this.coords) {
      let area = document.createElement("area");
      area.shape = "rect";
      area.id = "area" + item;
      area.coords = this.coords[item];
      area.style.zIndex = "3";
      area.onmouseenter = function() {
        jbod1.disks[item].diskHoverMe(area.coords)
      };
      area.onclick = function () {
        jbod1.disks[item].diskClickMe(area.coords);
      };
      area.onmouseleave = function () {
        jbod1.disks[item].diskUnhoverMe(area.coords)
      };
      this.mymap.appendChild(area)
    }
    divElement.appendChild(this.mymap);
  }

}


class harddrive{
  constructor(attributes) {
    this.attributes = attributes;
    this.img = '/static/images/12GBultrastarDrive.png';
  }

  diskClickMe(coords) {
    let index = this.attributes['index'];
    console.log(`You have clicked on disk at index ${index}`);
    console.log(coords)
    this.updateTooltip()
  }
  diskHoverMe(coords) {
    let index = this.attributes['index'];
    coords = coords.split(',');
    let posx = coords[0];
    let posy = coords[1];
    let width = +coords[2] - +coords[0];
    let height = +coords[3] - +coords[1];
    let highlight = document.getElementById("highlight");
    highlight.width = width.toString()
    highlight.height = height.toString()
    highlight.style.left = posx+'px';
    highlight.style.top = posy+'px';
    highlight.style.visibility = "visible";
    console.log(`You have hovered over disk with index ${index} `)

  }
  diskUnhoverMe(coords) {

   // let highlight = document.getElementById("highlight");
   //  highlight.style.visibility = "hidden";
    console.log(`You are no longer hovering over disk with index ${this.attributes['index']} `);

  }

  updateTooltip() {
    console.log("entering update tooltip.")
    let tooltip = document.getElementById("tooltip");
    //let tooltip = document.createElement("canvas");
    let cxt = tooltip.getContext("2d");
    cxt.font = "italic bold 15px arial"
    //cxt.fillText(`Index: ${this.attributes['index']} serial# ${this.attributes['serialnumber']}`,1,1)
    let width = tooltip.parentElement.clientWidth
    console.log(width)
    cxt.clearRect(0, 0, tooltip.width, tooltip.height);
    let lineHeight = 17;
    for(let attr in this.attributes){
      cxt.fillText(`${attr}: ${this.attributes[attr]}`,5,lineHeight,width);
      lineHeight = lineHeight + 17;
    }
  }


}

window.onload = function () {
    let ImageMap = function (map) {
            let n,
                areas = map.getElementsByTagName('area'),
                len = areas.length,
                coords = [],
                previousWidth = 1749;
            for (n = 0; n < len; n++) {
                coords[n] = areas[n].coords.split(',');
            }
            this.resize = function () {
                let n, m, clen,
                    //x = document.body.clientWidth / previousWidth;
                    x = document.getElementById("jbodimage").clientWidth / previousWidth;
                for (n = 0; n < len; n++) {
                    clen = coords[n].length;
                    for (m = 0; m < clen; m++) {
                        coords[n][m] *= x;
                    }
                    areas[n].coords = coords[n].join(',');
                }
                //previousWidth = document.body.clientWidth;
                previousWidth = document.getElementById("jbodimage").clientWidth
                return true;
            };
            window.onresize = this.resize;
        },
        imageMap = new ImageMap(document.getElementById('workmap'));
    imageMap.resize();
};


