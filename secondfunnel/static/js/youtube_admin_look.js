;(function($) {
    
    $(document).ready(function(){

         $('#changelist-filter').children('h3').each(function(){
            //for each filter list, collapse it
            $(this).click(function() {
                $(this).next().slideToggle();
            }).css(
               "cursor", "pointer"
            ).next().slideToggle();
        });

        $('iframe').filter(function(){ return $(this).attr('src').indexOf('youtube') > -1; }).each(function() {
            //for each youtube video on the page, record the aspect ratio
            $(this).attr('aspect', $(this).height() / $(this).width()).css('max-width', $(this).width());
        });

        $(window).resize();//intial call to resize in case videos are too large
    });
    
    $(window).resize(function() {
        //when a window resize is triggered, we want to resize the video accordingly if necessary
        var current_width = $(window).width();
        $('iframe').filter(function(){ return $(this).attr('src').indexOf('youtube') > -1; }).each(function() {
            //iterate over the yt video links, update width if video is too large
            if (current_width <= parseInt($(this).css('max-width'), 10)) {
                $(this).width(current_width).height($(this).attr('aspect') * current_width);
            }
        });
    }).resize();

})(django.jQuery);
