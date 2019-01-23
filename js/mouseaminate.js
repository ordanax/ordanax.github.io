function animate(elem){
    var effect = elem.data("effect");
    if(!effect || elem.hasClass(effect)) return false;
    elem.addClass(effect);
    setTimeout( function(){
        elem.removeClass(effect);
    }, 1000);
}
$(".animated").mouseenter(function() {
    animate($(this));
});