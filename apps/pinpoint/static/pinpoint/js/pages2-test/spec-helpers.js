beforeEach(function() {
   this.response = function(responseText, options) {
       var response;

       options = options || {};
       options.status = options.status || 200;
       options.headers = options.headers || {
           "Content-Type": "application/json"
       };
       options.callback = options.callback || 'fn';
       options.jsonp = options.jsonp || false;

       if (options.jsonp) {
           response = options.callback + '(' + JSON.stringify(responseText) + ')';
       } else {
           response = JSON.stringify(responseText);
       }

       return [
           options.status,
           options.headers,
           response
       ];
   };
});