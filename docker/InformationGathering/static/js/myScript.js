function myFunction() {
    var myCheckFF = document.getElementById("myCheckFF");
    var myCheckFS = document.getElementById("domain");
    var myCheckCW = document.getElementById("crawl");
    var myCheckPI = document.getElementById("platform");
    var myCheckCI = document.getElementById("cms");
    var myCheckIF = document.getElementById("finding");
    
    var blurList = [myCheckFS, myCheckCW,myCheckPI,myCheckCI,myCheckIF];

    if (myCheckFF.checked == true){
      blurList.forEach(function(item){
        item.checked = true;
        item.disabled = true;
      });
    }
    else if(myCheckFF.checked == false){
        blurList.forEach(function(item){
            item.disabled = false;
        });
    }
}  