// TODO: REWRITE TO BE COMPATIBLE WITH V3.0+ OF MASONRY
(function ($, window) {

    //==BEGIN HELPER FUNCTIONS==//
    //==END HELPER FUNCTIONS==//

    // BEGIN WILLET
    // Copy of base class _create method
    Masonry.prototype.__create__ = Masonry.prototype._create;
    Masonry.prototype._create = function() {
        this.__create__ = Masonry.prototype.__create__;
        this.__create__();

        this.getSize();
        this._getMeasurement( 'columnWidth', 'outerWidth' );
        this._getMeasurement( 'gutter', 'outerWidth' );
        this.measureColumns();
        var i = this.cols;
        this.offsetYs = [];

        while (i--) { 
            this.offsetYs.push( 0 );
        }

        if ( this.options.isSmartNodes ) {
            var instance = this;
            $(window).on('scroll resize mousewheel', function(){
                setTimeout(function(){
                    //instance._infiniteScrollCleanup();
                }, 1);
            });
        }
    }
    // END WILLET


    Masonry.prototype._layoutItems = function( items, isInstant ) {
        if ( !items || !items.length ) {
            // no items, emit event with empty array
            this.emitEvent( 'layoutComplete', [ this, items ] );
            return;
        }

        // emit layoutComplete when done
        this._itemsOn( items, 'layout', function onItemsLayout() {
                this.emitEvent( 'layoutComplete', [ this, items ] );
        });

        // BEGIN WILLET
        this.recent = this.recent || [];
        var queue = [],
            dupes, instagramImg;


        for ( var i = 0, len = items.length; i < len; i++ ) {
            var item = items[i],
                $item = $(item.element);
            // Check to see if we've recently included this instagram image, if we
            // have, we'll want to skip it here.
            instagramImg = $item.find(':not(.social-buttons) img').prop('src');
            dupes = _.filter(this.recent, function($elem) {
                var elemImg = $elem.find(':not(.social-buttons) img').prop('src');
                return (elemImg == instagramImg);
            });
            
            if (dupes.length != 0) {
                item.remove();
                // remove item from collection
                var index = this.items.indexOf(item);
                this.items.splice(index, 1);
                continue;
            }
            // END WILLET
            // get x/y object from method
            var position = this._getItemLayoutPosition( item );
            // enqueue
            position.item = item;
            position.isInstant = isInstant;
            queue.push( position );
        }

        this._processLayoutQueue( queue );
    };

    Masonry.prototype._getItemLayoutPosition = function (item) {
        item.getSize();
        // how many columns does this brick span
        var colSpan = Math.ceil(item.size.outerWidth / this.columnWidth );
        colSpan = Math.min(colSpan, this.cols);
        var colGroup = this._getColGroup(colSpan);
        // get the minimum Y value from the columns
        var minimumY = Math.min.apply(Math, colGroup),
            shortColIndex = colGroup.indexOf(minimumY);
        
        // BEGIN WILLET
        /*
         *   We need to ensure that the short column is NOT an odd numbered
         *   column, so, we may need to find the second shortest column
         * */
        // get the minimum Y value from the columns
        var dupeGroupY = colGroup.slice(0),
            minYObjs = [];
        for (var k = 0; k < dupeGroupY.length; k++) {
            minYObjs.push({
                'column': k,
                    'value': dupeGroupY[k]
            });
        }

        minYObjs.sort(function (a, b) {
            if (a.value !== b.value) {
                return a.value - b.value;
            } else {
                return a.column - b.column;
            }
        });

        // Iterate over all the minimums...
        for (var l = 0, len = minYObjs.length; l < len; l++) {
            var obj = minYObjs[l];
            shortColIndex = obj.column;
            minimumY = obj.value;

            if (item.element.className.indexOf('youtube') > -1 && (shortCol % 2 !== 0)) {
                continue;
            } else {
                break;
            }
        }

        // Determine if we're offseted.
        var x = this.columnWidth * shortColIndex,
            colSpan = this._getColSpan( item ),
            col = 0;

        while (col * this.columnWidth < x) ++col;

        var y = Math.min.apply(Math, this.offsetYs.slice(col, col + colSpan));
        if (minimumY == -Infinity || y == Infinity) {
            y = minimumY;
        } else {
            y = minimumY + y;
        }

        // END WILLET
        // position the brick
        var position = {
            'x': x,
            'y': y
        };

        // apply setHeight to necessary columns
        var setHeight = y + item.size.outerHeight,
            setSpan = this.cols + 1 - colGroup.length;
        for (i = 0; i < setSpan; i++) {
            this.colYs[shortColIndex + i] = setHeight;
        }
        return position;
    };

    // BEGIN WILLET
    Outlayer.Item.prototype._getColumn = function() {
        var colSpan = this.layout._getColSpan( this ),
            col = 0;

        while ( col * this.layout.columnWidth < this.position.x ) {
            ++col;
        }
        return col;
    };

    Masonry.prototype._getColSpan = function( item ) {
        item.getSize();
        var colSpan = Math.ceil(item.size.outerWidth / this.columnWidth );
        return Math.min( colSpan, this.cols );
    };

    Masonry.prototype._infiniteScrollCleanup = function () {
        /* Cleans up unused DOM nodes in the Infinite Scroll
           Begin by cleaning up the DOM nodes that are no longer visible.
           Afterwards add back DOM nodes that have travelled into the line
           of sight. */
        var upper_threshold = $(window).scrollTop() - $(window).height(),
            lower_threshold = $(window).scrollTop() + 2 * $(window).height(),
            indices = [],
            _isVisible = function( obj ) { 
                return !(obj.size.height + obj.position.y < upper_threshold || obj.position.y > lower_threshold);
            },
            instance = this;
        
        // Off-screen DOM nodes
        this.offscreen = this.offscreen || [];
        
        for ( var i = 0; i < this.items.length; ++i ) {
            // item.position.x/y are saved with the LayoutItem, which saves us that
            // work.
            var item = this.items[i];
            // Get size, just in case
            item.getSize();

            if (!_isVisible(item)) {
                // It is out of the screen, knock it out!
                // Add to our list of elements
                // Remove from the Masonry instance
                var index = this.items.indexOf(item),
                    copy = item.element.cloneNode(true),
                    col = item._getColumn(),
                    colSpan = this._getColSpan( item );
                
                if (!(item.position.y > lower_threshold)) {
                    // Only need/want to adjust for items above our view
                    for ( var j = col; j < colSpan + col; ++j ) {
                        this.offsetYs[j] = Math.max(this.offsetYs[j], item.position.y + item.size.height);
                    }
                }
                this.element.removeChild(item.element);
                item.element = copy;
                indices.push(item);
                this.offscreen.push(item);       
            }
        }

        for (var i = 0; i < indices.length; ++i) {
            var item = indices[i],
                index = this.items.indexOf(item);
            console.log(index);
            this.items.splice(index, 1);
        }

    };
    // END WILLET


})(jQuery, window);