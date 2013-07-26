// START WILLET
// Custom Matchers for the Willet Project
beforeEach(function(){
    this.addMatchers({
        toContainOnce: function( elem ) {
            var copies = 0,
                arr = this.actual,
                notText = this.isNot ? " not" : "";
            
            if (!arr.length || arr.length == 0) {
                return true;
            }

            for (var i = 0; i < arr.length; ++i) {
                if (JSON.stringify(arr[i]) === JSON.stringify(elem)) {
                    ++copies;
                }
            }

            this.message = function () {
                return "Expected " + arr.toString() + " to " + notText + " " + 
                contain + " " + elem.toString() + " only once, but found " + copies + " times.";
            };

            return copies <= 1;
        },
        
        toContainUnique: function() {
            var arr = this.actual;
            var notText = this.isNot ? " not" : "";
            
            this.message = function() {
                return "Expected the array to contain only unique values";
            };

            for (var i = 0; i < arr.length; ++i) {
                for (var j = i + 1; j < arr.length; ++j){
                    if (JSON.stringify(arr[i]) == JSON.stringify(arr[j])) {
                        return false;
                    }
                }
            }
            return true;
        }
    });
});
// END WILLET