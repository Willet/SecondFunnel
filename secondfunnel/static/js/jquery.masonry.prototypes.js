/* JQuery Masonry Prototype functions
 *
 * Provided Option: smartNodes
 * To-Use: Specify "smartNodes: True" when creating the Masonry instance.
 *
 * Implementation Details:
 *    These prototype functions extend Masonry to allow it to perform self-cleanup, that is it removes elements
 * from its instance and the DOM when the elements are no longer visible to the user.  These elements are re-added
 * in the same order when they become visible again.
 *
 */
(function(window, $, undefined) {   
    /* 
     * smartscroll: debounced scroll event for jQuery *
     * https://github.com/lukeshumard/smartscroll
     * based on smartresize by @louis_remi: https://github.com/lrbabe/jquery.smartresize.js *
     * Copyright 2011 Louis-Remi & lukeshumard * Licensed under the MIT license. *
     */

    var event = $.event,
        scrollTimeout;

    event.special.smartscroll = {
        setup: function() {
            $(this).bind( "scroll", event.special.smartscroll.handler );
        },
        teardown: function() {
            $(this).unbind( "scroll", event.special.smartscroll.handler );
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
            }, execAsap === "execAsap"? 0 : 10);
        }
    };

    $.fn.smartscroll = function( fn ) {
        return fn ? this.bind( "smartscroll", fn ) : this.trigger( "smartscroll", ["execAsap"] );
    };


    //=============================MASONRY PROTOTYPES=================================================================

    // Helper functions
    function above( $brick, bottom ) {
        /* Returns true if element is above our visible area.
           @return boolean */
        var upper_threshold = $(window).scrollTop() - $(window).height(),
            bottom          = bottom || ($brick.offset().top + $brick.height());
        return bottom < upper_threshold;
    }

    function below( $brick, top ) {
        /* Returns true if element is below our visible area.
           @return boolean */
        var lower_threshold = $(window).scrollTop() + 2 * $(window).height(),
            top             = top || $brick.offset().top;
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
                this.colYs.push( 0 );
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
            'y': this.offset.y,
        };        
            
        if ( this.options.smartNodes ) {
            this.options.isKnockingOut = false;
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
        if ( this.options.isKnockingOut ) {
            return;
        } else {
            this.options.isKnockingOut = true;
            this._knockout();
            this.options.isKnockingOut = false;
        }
    };

    $.Mason.prototype._knockout = function() {
        // Handle Masonry and DOM cleanup by what is visible and not visible on the screen.
        var destroyed = 0,
            instance  = this;
        
        this.$bricks.each(function() {
            // For each block that is no longer in view, knock it into our saved arrays
            // and increment our counter; only want to reload when stuff have been destroyed.
            var $brick = $(this),
                deconstruct = function( $obj ) {
                    destroyed++;
                    return { 'top': $obj.offset().top, 'left': $obj.position().left, 
                             'bottom': $obj.offset().top + $obj.height(), 'offsetTop': $obj.position().top, 'obj': $obj.detach() }
                };
            if ( above($brick) ) {
                instance.nodes['above'].push(deconstruct($brick));
            } else if ( below($brick) ) {
                instance.nodes['below'].push(deconstruct($brick));
            }
        });

        if ( destroyed > 0 ) {
            // Apply positioning logic and reload the blocks
            this.reloadItems();
            this.relativeOffset.y = this.element.children().first().position().top;
            this.reload();
        }
        //Lastly, check if we need to reinsert stuff
        this._reInsert();
    };

    // Extend the Masonry instance to allow detached/deconstructed bricks to be added back to the instance
    // when they should be visible.
    $.Mason.prototype._reInsert = function() {
        // This method allows content to be inserted to the top of the Masonry instance.  Particularly effective
        // when combined with SmartNodes.
        var nodes       = [],
            instance    = this,
            constructed = 0,
            construct   = function( properties ) {
                constructed++;
                return $(properties.obj).css({'top': properties.offsetTop, 'left': properties.left});
            };
        // Now check both arrays.
        $.each(this.nodes['above'], function(index, properties) {
            if (!above(undefined, properties.bottom)) {
                instance.relativeOffset.y = Math.min(instance.relativeOffset.y, properties.offsetTop);
                instance.element.prepend(construct( properties ));
            } else {
                nodes.push(properties);
            }
        });
        this.nodes['above'] = nodes;
        nodes = [];
        
        $.each(this.nodes['below'], function(index, properties) {
            if (!below(undefined, properties.top)) {
                instance.element.append(construct( properties ));
            } else {
                nodes.push(properties);
            }
        });
        this.nodes['below'] = nodes;
        // Reload the instance if we actually constructed something
        if ( constructed > 0 ) this.reload();
    };

})(window, jQuery);