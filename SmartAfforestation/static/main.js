function loaderWidget(){
    var loader = document.getElementById("loader");
    var mainbody = document.getElementById("mainbody");
    mainbody.style.opacity = "0.3";
    mainbody.style.pointerEvents = "none";
    loader.style.display = "block";
    var time = parseInt(document.getElementsByName("runtime")[0].value);
    setTimeout(()=>{
        mainbody.style.pointerEvents = "auto";
        loader.style.display = "none"; 
        mainbody.style.opacity = "1";
    }, time*1000);
}
