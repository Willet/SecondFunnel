/**
 * JQuery Masonry Prototype Functions
 *
 * Provided Option: smartNodes
 * To-Use: Specify "smartNodes: True" when creating the Masonry instance.
 *
 * Implementation Details:
 *    These prototype functions extend Masonry to allow it to perform self-cleanup, that is, it removes elements
 * from its instance and the DOM when the elements are no longer visible to the user.  These elements are re-added
 * in the same order when they become visible again.
 *
 * Copyright 2013 Willet Inc.
 */
(function(window, $, undefined) {   
    //=============================HELPER FUNCTIONS========================================================================================
    function outOfScreen( top, bottom ) {
        var upper_threshold = $(window).scrollTop() - $(window).height(),
            lower_threshold = $(window).scrollTop() + 2 * $(window).height();
        return bottom < upper_threshold || top > lower_threshold;
    }
    //=============================MASONRY FUNCTIONS & EXTENDED PROTOTYPES=================================================================
    
    // Rewrite default functions to allow for the changes we are making.
    // Change how layouts work.
    $.Mason.prototype._reLayout = function( callback ) {
        // Reset the columns using our relativeOffset
        this.colYs = [];
        for ( var i = 0; i < this.cols; i++ ) {
            this.colYs.push( this.relativeOffset.y[i] );
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
            $(window).bind('scroll mousewheel wheel', function() {
                instance.knockout();
            });
        }
        this.min_height = this.element.height();
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

    $.Mason.prototype._updateColVals = function() {
        // Get the minimum offset of each column relative to the container.
        var instance    = this,
            minColVals  = [],
            maxColVals  = [];
        // Initialize the array of arrays
        this.reloadItems();
        for ( var col = 0; col < this.cols; col++ ) {
            minColVals.push([]);
            maxColVals.push([]);
        }
        $.each(this.$bricks, function() {
            // Can't access attributes via jquery CSS for some reason.  Maybe a problem with JQuery 1.8.3?  Use
            // position instead.
            var $brick     = $(this),
                brickLeft  = $brick.position().left,
                brickTop   = $brick.position().top,
                brickWidth = $brick.width(),
                colSpan    = Math.min(instance.cols, Math.ceil( $brick.outerWidth(true) / instance.columnWidth )),
                col        = 0;
            while (col * instance.columnWidth < brickLeft) ++col;
            for ( var i = col; i < col + colSpan; ++i ) {
                minColVals[i].push(brickTop);
                maxColVals[i].push(brickTop + $brick.outerHeight(true));
            }
        });
        for ( var col = 0; col < this.cols; col++ ) {
            minColVals[col] = (minColVals[col].length == 0? this.relativeOffset.y[col] : Math.min.apply(Math, minColVals[col]));
            maxColVals[col] = (maxColVals[col].length == 0? this.colYs[col] : Math.max.apply(Math, maxColVals[col]));
        }
        this.relativeOffset.y = minColVals;
        this.colYs = maxColVals;
    };

    // Start the code for the knockout logic and handling; a prototype function that provides Masonry with the ability
    // to cleanup elemenets from the DOM that are no longer visible.  We have to extend Masonry to allow for the method
    // to be called on resizes and scrolls.
    $.Mason.prototype.knockout = function() {
        if ( this.isLaidOut ) {
            $(this).queue(function(next) {
                var instance = this;
                instance._knockout();
                $('#nodecount').text(instance.element.children().length + instance.nodes.length);
                $('#domcount').text(instance.element.children().length);
                next();
            });
        }
    };

    $.Mason.prototype._knockout = function() {
        // Handle Masonry and DOM cleanup by what is visible and not visible on the screen.
        var instance    = this,
            destroyed   = 0,
            deconstruct = function ( $obj ) {
                var properties = { top: $obj.offset().top, 
                                   width: $obj.width(),
                                   height: $obj.height(),
                                   left: $obj.offset().left,
                };
                destroyed++;
                properties.obj = $obj.detach();
                return properties;
            };
        this.element.children().each(function() {
            var $brick = $(this);
            if (outOfScreen($brick.offset().top, $brick.offset().top + $brick.height())) {
                // Ignore animated content, we don't know how it will be laid out yet
                if (!($brick.is(':animated'))) {
                    instance.nodes.push(deconstruct($brick));
                }
            }
        });
        if ( destroyed > 0 ) this._updateColVals();
        this._reInsert();
    };


    $.Mason.prototype._collides = function( a, $bricks ) {
        var collision   = false,
            getPosition = function( $brick ) {
                return { top: $brick.offset().top,
                         width: $brick.width(),
                         height: $brick.height(),
                         left: $brick.offset().left };
            }; 
        $bricks.each(function(){
            var b = getPosition($(this));
            // http://stackoverflow.com/questions/2440377/javascript-collision-detection
            if ($(this).is(':animated')) {
                // Pass if it's animated
            } else if (!(((a.top + a.height) < (b.top)) || (a.top > (b.top + b.height)) || 
                         ((a.left + a.width) < b.left) || (a.left > (b.left + b.width)))) {
                collision = true;
                return false;
            }
        });
        return collision;
    };

    // Extend the Masonry instance to allow detached/deconstructed bricks to be added back to the instance
    // when they should be visible.
    $.Mason.prototype._reInsert = function() {
        // This method allows content removed by _knockout to be re-inserted into the Masonry instance in thier
        // original positions.
        var instance        = this,
            constructed     = 0,
            collidedBricks  = [],
            construct       = function( fn, properties ) {
                var $brick  = $(properties.obj);
                constructed++;
                if (instance._collides(properties, instance.element.children())) {
                    collidedBricks.push($brick);
                } else {
                    instance.element[fn]($brick);
                }
            };
        // Now check the array of nodes.
        var new_nodes = $.grep(this.nodes, function(properties, index) {
            var fn = (properties.top + properties.height < $(window).scrollTop()? 'prepend' : 'append');
            if (!outOfScreen(properties.top, properties.top + properties.height)) {
                construct(fn, properties);
                return false;
            }
            return true;
        });
        this.nodes = new_nodes;
        if ( constructed > 0 ) {
            this._updateColVals();
            if ( collidedBricks.length > 0 ) {
                // If we had a collision, we want to add the elements that collided after the elements they
                // collided with.
                var instance = this;
                $.each(collidedBricks, function(index, $brick){
                    instance.element.append($brick);
                    instance.appended($brick, true);
                });
                this._updateColVals(); // Need two updates in this case
            }
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
        this.min_height = Math.max(this.min_height, Math.max.apply(Math, this.colYs));
        containerSize.height = this.min_height;
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