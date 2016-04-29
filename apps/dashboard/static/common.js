// Used to get CSRF Token Cookie so django will allow us to use do API calls
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function toTitleCase(str){
    return str.split(" ").map(function(i){return i[0].toUpperCase() + i.substring(1).toLowerCase()}).join(" ");
}

$(document).ready(function(){
    //var Forms = new formView();
    $.ajaxSetup({
        headers: { 
            "X-CSRFToken": getCookie("csrftoken"),
            "Cache-Control": 'max-age=10'
        },
        cache: false,

    });
});
