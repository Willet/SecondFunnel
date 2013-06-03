/**
 * JQuery Masonry Prototype Functions
 *
 * Provided Option: smartNodes
 * To-Use: Specify "smartNodes: True" when creating the Masonry instance.
 *
 * Implementation Details:
 *    These prototype functions extend Masonry to allow it to perform self-cleanup, that is it removes elements
 * from its instance and the DOM when the elements are no longer visible to the user.  These elements are re-added
 * in the same order when they become visible again.
 *
 * Copyright 2013 Willet Inc.
 */
(function(window, $, undefined) {   
    /* 
     * smartscroll: debounced scroll event for jQuery *
     * https://github.com/lukeshumard/smartscroll
     * based on smartresize by @louis_remi: https://github.com/lrbabe/jquery.smartresize.js *
     * Copyright 2011 Louis-Remi & lukeshumard * Licensed under the MIT license. *
     */

    var event = $.event,
        scrollevents = "scroll mousewheel wheel",
        scrollTimeout;

    event.special.smartscroll = {
        setup: function() {
            $(this).bind( scrollevents, event.special.smartscroll.handler );
        },
        teardown: function() {
            $(this).unbind( scrollevents, event.special.smartscroll.handler );
        },
        handler: function( event, execAsap ) {
            // Save the context
            var context = this,
            args = arguments;

            // set correct event type
            event.type = "smartscroll";

            if (scrollTimeout) { clearTimeout(scrollTimeout); }
            scrollTimeout = setTimeout(function() {
                jQuery.event.handle.apply( context, args );
            }, execAsap === "execAsap"? 0 : 0);
        }
    };

    $.fn.smartscroll = function( fn ) {
        return fn ? this.bind( "smartscroll", fn ) : this.trigger( "smartscroll", ["execAsap"] );
    };


    //=============================MASONRY FUNCTIONS & EXTENDED PROTOTYPES=================================================================
    
    // Helper functions
    function above( $brick, bottom ) {
        /* Returns true if element is above our visible area.
           @return boolean */
        var upper_threshold = $(window).scrollTop() - $(window).height();
        bottom = bottom || ($brick.offset().top + $brick.height());
        return bottom < upper_threshold;
    }

    function below( $brick, top ) {
        /* Returns true if element is below our visible area.
           @return boolean */
        var lower_threshold = $(window).scrollTop() + 2 * $(window).height();
        top = top || $brick.offset().top;
        return top > lower_threshold;
    }

    // Rewrite default functions to allow for the changes we are making.
    // Change how layouts work.
    $.Mason.prototype._reLayout = function( callback ) {
        // reset columns
        var i = this.cols;
        this.colYs = [];
        while (i--) {
            if ( this.relativeOffset )
                this.colYs.push( this.relativeOffset.y );
            else
                this.colYs.push( this.offset.y );
        }
        // apply layout logic to all bricks
        this.layout( this.$bricks, callback );
    };

    // Extend Masonry to allow our new function to be called by modifying the create parameter/function
    // to allow for our additional variables.
    $.Mason.prototype.__create__ = $.Mason.prototype._create;
    $.Mason.prototype._create = function( options ) {
        var instance = this;
        this.__create__( options );
        this.nodes = { 'above': [],
                       'below': [] };
        this.relativeOffset = {
            'x': this.offset.x,
            'y': this.offset.y,
        };        
        if ( this.options.smartNodes ) {
            $(window).bind('smartscroll.masonry', function() {
                instance.knockout();
            });
        }
    };

    $.Mason.prototype.resize = function() {
        var prevColCount = this.cols;
        // get updated colCount
        this._getColumns();
        if ( this.isFluid || this.cols !== prevColCount ) {
            // if column count has changed, trigger new layout
            this._reLayout();
            // if smartNodes are on, check if we need to reapply the logic
            if ( this.options.smartNodes ) {
                this.knockout();
            }
        }
    };


    // Start the code for the knockout logic and handling; a prototype function that provides Masonry with the ability
    // to cleanup elemenets from the DOM that are no longer visible.  We have to extend Masonry to allow for the method
    // to be called on resizes and scrolls.
    $.Mason.prototype.knockout = function() {
        // Convenience method
        this._knockout();
    };

    $.Mason.prototype._knockout = function() {
        // Handle Masonry and DOM cleanup by what is visible and not visible on the screen.
        var destroyed = 0,
            instance  = this;
        
        this.$bricks.each(function() {
            // For each block that is no longer in view, knock it into our saved arrays
            // and increment our counter; only want to reload when stuff have been destroyed.
            var $brick      = $(this),
                key         = above($brick)? 'above' : (below($brick)? 'below': undefined),
                deconstruct = function( $obj ) {
                    destroyed++;
                    return { 'top': $obj.offset().top, 'left': $obj.position().left, 
                             'bottom': $obj.offset().top + $obj.height(), 'offsetTop': $obj.position().top, 'obj': $obj.detach() }
                };
            if ( key ) instance.nodes[key].push(deconstruct($brick));
        });

        if ( destroyed > 0 ) {
            this.$bricks = this._getBricks( this.element.children() );
            // In the case of really fast scrolling, we need to wait until we can actually grab the children, as
            // children might be being positioned in the instance while additional scrolling events are triggered.
            var waitForChildren = function() {
                if (!(instance.element.children().first().position())) setTimeout(waitForChildren, 1);
                else instance.relativeOffset.y = instance.element.children().first().position().top;
            };
            waitForChildren();
        }
        //Lastly, check if we need to reinsert stuff
        this._reInsert();
    };

    // Extend the Masonry instance to allow detached/deconstructed bricks to be added back to the instance
    // when they should be visible.
    $.Mason.prototype._reInsert = function() {
        // This method allows content removed by _knockout to be re-inserted into the Masonry instance in thier
        // original positions.
        var instance    = this,
            constructed = 0,
            construct   = function( properties ) {
                constructed++;
                return $(properties.obj).css({'top': properties.offsetTop, 'left': properties.left});
            };
        // Now check both arrays.
        $.each(['above', 'below'], function(index, key) {
            instance.nodes[key] = $.grep(instance.nodes[key], function(properties, index) {
                var test     = (key == 'above'? above : below),
                    fn       = (key == 'above'? 'prepend' : 'append'),
                    property = properties[(key == 'above'? 'bottom': 'top')];
                if (!test(undefined, property)) {
                    instance.relativeOffset.y = Math.min(instance.relativeOffset.y, properties.offsetTop);
                    instance.element[fn](construct( properties ));
                    return false;
                }
                return true;
            });
        });
        // Reload the instance if we actually constructed something
        if ( constructed > 0 ) this.reload();
    };


    /*
     * jQuery Masonry v2.1.08 layout
     * http://masonry.desandro.com
     *
     * Licensed under the MIT license.
     * Copyright 2012 Davide DeSandro
     */
    $.Mason.prototype.layout = function( $bricks, callback ) {
        
        // place each brick
        for (var i=0, len = $bricks.length; i < len; i++) {
            this._placeBrick( $bricks[i] );
        }
      
        // set the size of the container
        var containerSize = {};
        containerSize.height = Math.max(this.element.height(), Math.max.apply( Math, this.colYs ));
        if ( this.options.isFitWidth ) {
            var unusedCols = 0;
            i = this.cols;
            // count unused columns
            while ( --i ) {
                if ( this.colYs[i] !== 0 ) {
                    break;
                }
                unusedCols++;
            }
            // fit container to columns that have been used;
            containerSize.width = (this.cols - unusedCols) * this.columnWidth - this.options.gutterWidth;
        }
        this.styleQueue.push({ $el: this.element, style: containerSize });

        // are we animating the layout arrangement?
        // use plugin-ish syntax for css or animate
        var styleFn = !this.isLaidOut ? 'css' : (
                                                 this.options.isAnimated ? 'animate' : 'css'
                                                 ),
        animOpts = this.options.animationOptions;

        // process styleQueue
        var obj;
        for (i=0, len = this.styleQueue.length; i < len; i++) {
            obj = this.styleQueue[i];
            obj.$el[ styleFn ]( obj.style, animOpts );
        }

        // clear out queue for next time
        this.styleQueue = [];

        // provide $elems as context for the callback
        if ( callback ) {
            callback.call( $bricks );
        }
      
        this.isLaidOut = true;
    };

})(window, jQuery);