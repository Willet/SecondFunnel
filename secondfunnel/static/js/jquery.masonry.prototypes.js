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

    //=============================HELPER FUNCTIONS========================================================================================
    function screenout( $brick, top, bottom ) {
        var upper_threshold = $(window).scrollTop() - $(window).height(),
            lower_threshold = $(window).scrollTop() + 2 * $(window).height();
        bottom = bottom || ($brick.offset().top + $brick.height());
        top    = top || $brick.offset().top;
        return bottom < upper_threshold || top > lower_threshold;
    }

    function screenin( $brick, top, bottom ) {
        return !(screenout($brick, top, bottom));
    }

    //=============================MASONRY FUNCTIONS & EXTENDED PROTOTYPES=================================================================
    
    // Rewrite default functions to allow for the changes we are making.
    // Change how layouts work.
    $.Mason.prototype._reLayout = function( callback ) {
        // reset columns
        this.colYs = [];
        for ( var i = 0; i < this.cols; i++ ) {
            if ( this.relativeOffset )
                this.colYs.push( this.relativeOffset.y[i] );
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
        this.nodes = [];
        this.relativeOffset = {
            'y': [],
        };
        this._getColumns();
        for ( var i = 0; i < this.cols; i++ ) this.relativeOffset.y.push( this.offset.y );
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

    $.Mason.prototype._updateColYs = function() {
        var instance = this;
        this.reloadItems();
        this._getColumns();
        for ( var col = 0; col < this.cols; col++ ) {
            // Find the minimumY for each column.
            var minimumColYs = $.grep(this.$bricks, function(el, i) {
                var colOffset = col * instance.columnWidth,
                    $el       = $(el),
                    elOffset  = parseInt($el.css('left'), 10);
                return elOffset == colOffset || (elOffset <= colOffset && elOffset + $el.width() >= colOffset);
            });
            for ( var i = 0; i < minimumColYs.length; i++ ) minimumColYs[i] = parseInt($(minimumColYs[i]).css('top'), 10);
            this.relativeOffset.y[col] = (minimumColYs.length == 0?  this.offset.y : Math.min.apply(Math, minimumColYs));
        }
    };

    $.Mason.prototype._knockout = function() {
        // Handle Masonry and DOM cleanup by what is visible and not visible on the screen.
        var destroyed = 0,
            instance  = this;
        
        this.$bricks.each(function() {
            // For each block that is no longer in view, knock it into our saved arrays
            // and increment our counter; only want to reload when stuff have been destroyed.
            var $brick      = $(this),
                deconstruct = function( $obj ) {
                    destroyed++;
                    return { 'top': $obj.offset().top, 'left': $obj.position().left, 
                             'bottom': $obj.offset().top + $obj.height(), 'offsetTop': $obj.position().top, 'obj': $obj.detach() }
                };
            if (screenout($brick)) instance.nodes.push(deconstruct($brick));
        });

        if ( destroyed > 0 ) this._updateColYs();
        //Lastly, check if we need to reinsert stuff
        this._reInsert();
    };

    // Extend the Masonry instance to allow detached/deconstructed bricks to be added back to the instance
    // when they should be visible.
    $.Mason.prototype._reInsert = function() {
        // This method allows content removed by _knockout to be re-inserted into the Masonry instance in thier
        // original positions.
        var instance    = this,
            $bricks      = $(),
            construct   = function( properties ) {
                var $brick = $(properties.obj).offset({'top': properties.top}).css({'top': properties.offsetTop, 'left': properties.left});
                $bricks.add($brick);
                return $brick;
            };
        // Now check the array of nodes.
        var new_nodes = $.grep(this.nodes, function(properties, index) {
            var fn = (properties.bottom < $(window).scrollTop()? 'prepend' : 'append');
            if (screenin(undefined, properties.top, properties.bottom)) {
                instance.element[fn](construct( properties ));
                return false;
            }
            return true;
        });
        this.nodes = new_nodes;
        if ( $bricks[0] !== undefined ) {
            this._updateColYs();
            this.layout($bricks);
        }
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
        containerSize.height = Math.max(this.element.innerHeight(), Math.max.apply( Math, this.colYs ));
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