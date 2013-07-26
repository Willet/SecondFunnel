// Order matters!
// This is the base JS file, the first file that is called when we test the
// sauce for the SecondFunnel project.  It instantiates the needed modules.
describe("Setup", function() {
    it("setup", function() {
        (Willet.browser=Willet.browser||{}).mobile = false;

        $(document).bind("mobileinit", function () {
            $.mobile.autoInitializePage = false;
        });

        if (Willet.browser.mobile) {
            $(function () {
                $.mobile.initializePage();
            }); 
        }   
    
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
        }
        // Want to disable Page Scrolling for our Unit Tests
        PAGES.__pageScroll__ = PAGES.pageScroll;
        PAGES.pageScroll = function() { return; };
        
        PAGES.attachListeners();
        $('.discovery-area').masonry({
            itemSelector: '.block',
            
            columnWidth: function (containerWidth) {
                return containerWidth / 4;
            },
            
            isResizable: true,
            isAnimated: true
        });

        var callback = jasmine.createSpy("init");
        expect(Willet.mediator.fire).toBeDefined();

        runs(function(){
            Willet.mediator.fire('IR.init', []);
            Willet.mediator.fire('IR.changeSeed', []);
            Willet.mediator.fire('IR.getInitialResults', [callback]);
        });

        waitsFor(function() {
            return callback.callCount > 0;
        }, "initial results to load", 5000); 

        runs(function(){
            expect(callback.callCount).toEqual(1);
        });
    });
});
