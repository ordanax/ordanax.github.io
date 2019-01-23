// Плавная прокрутка. Скорость прокуртки определяется праметром 1500
$(function(){
        $("a[href^='#']").click(function(){
                var _href = $(this).attr("href");
                $("html, body").animate({scrollTop: $(_href).offset().top+"px"},1500);
                return false;
        });
});