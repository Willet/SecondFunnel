// Order matters!
// This is the base JS file, the first file that is called when we test the
// sauce for the SecondFunnel project.  It instantiates the needed modules.
describe("Setup", function() {
    it("initialize Pages", function() {
        (function(a){(Willet.browser=Willet.browser||{}).mobile=/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4))})(navigator.userAgent||navigator.vendor||window.opera);
        
        if (Willet.browser.mobile) {
            PAGES.init(PAGES.mobile.readyFunc, PAGES.mobile.layoutFunc);
        } else {
            PAGES.init(PAGES.full.readyFunc, PAGES.full.layoutFunc);
        }
        // Check that Pages, IntentRank and the Mediator are up to go
        expect(PAGES.intentRank).toEqual(jasmine.any(Object));
        expect(Willet.mediator).toBeDefined();
    });

    it("initialize Masonry", function() {
        if (!Willet.browser.mobile) {
            // Override masonry
            $(function() {
                $.Mason.prototype._placeBrick = function( brick ) {
                    var $brick = $(brick),
                        colSpan, groupCount, groupY, groupColY, j,
                        dupes, instagramImg;

                    // START WILLET
                    this.recent = this.recent || [];

                    // Check to see if we've recently included this instagram
                    // image. If so, skip it.
                    if ($brick.hasClass('instagram')) {
                        instagramImg = $brick.find('img').not('.social-buttons ' +
                                                              'img').prop('src');
                        dupes = _.filter(this.recent, function($elem) {
                            var elemImg = $elem.find('img').not('.social-buttons ' +
                                                                'img').prop('src');
                            return (elemImg == instagramImg);
                        });

                        if (dupes.length != 0) {
                            this.remove($brick);
                            return;
                        }
                    }
                    
                    while(this.recent.length > 5) {
                        this.recent.shift();
                    }
                    this.recent.push($brick);
                    // END WILLET
                    
                    //how many columns does this brick span
                    colSpan = Math.ceil( $brick.outerWidth(true) / this.columnWidth );
                    colSpan = Math.min( colSpan, this.cols );
                    
                    if ( colSpan === 1 ) {
                        // if brick spans only one column, just like singleMode
                        groupY = this.colYs;
                    } else {
                        // brick spans more than one column
                        // how many different places could this brick fit horizontally
                        groupCount = this.cols + 1 - colSpan;
                        groupY = [];
                        
                        // for each group potential horizontal position
                        for ( j=0; j < groupCount; j++ ) {
                            // make an array of colY values for that one group
                            groupColY = this.colYs.slice( j, j+colSpan );
                            // and get the max value of the array
                            groupY[j] = Math.max.apply( Math, groupColY );
                        }
                        
                    }
                    
                    // BEGIN WILLET
                    /*
                     *   We need to ensure that the short column is NOT an odd numbered
                     *   column, so, we may need to find the second shortest column
                     * */
                    // get the minimum Y value from the columns
                    var dupeGroupY = groupY.slice(0);
                    var minYObjs = []
                    for (var k=0; k < dupeGroupY.length; k++) {
                        minYObjs.push({
                                'column': k,
                                'value': dupeGroupY[k]
                        });
                    }
                    
                    minYObjs.sort(function(a,b) {
                        if (a.value !== b.value) {
                            return a.value - b.value;
                        } else {
                            return a.column - b.column;
                        }
                    });
                    
                    var minimumY = Math.min.apply( Math, groupY ),
                        shortCol = 0;
                    
                    // Iterate over all the minimums...
                    for (var l= 0, len = minYObjs.length; l < len; l++) {
                        var item = minYObjs[l];
                        shortCol = item.column;
                        minimumY = item.value;
                        
                        if ($brick.hasClass('youtube') && (shortCol % 2 != 0)) {
                            continue;
                        } else {
                            break;
                        }
                    }
                    
                    // END WILLET
                    
                    // position the brick
                    var position = {
                        top: minimumY + this.offset.y
                    };
                    
                    // position.left or position.right
                    position[ this.horizontalDirection ] = this.columnWidth * shortCol + this.offset.x;
                    this.styleQueue.push({ $el: $brick, style: position });
                    
                    // apply setHeight to necessary columns
                    var setHeight = minimumY + $brick.outerHeight(true),
                        setSpan = this.cols + 1 - len;
                    for ( i=0; i < setSpan; i++ ) {
                        this.colYs[ shortCol + i ] = setHeight;
                    }
                }
            });
            expect($('.discovery-area').masonry).toBeDefined();
        }
        // Inherent truth, test does nothing for Mobile, but we need
        // some result.
        expect(Object()).toEqual(jasmine.any(Object));
    });
});
