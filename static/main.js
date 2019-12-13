function loaderWidget(){
    var loader = document.getElementById("loader");
    loader.style.display = "block";
    var time = parseInt(document.getElementsByName("runtime")[0].value);
    setTimeout(()=>{ loader.style.display = "none" }, time*1000);
}