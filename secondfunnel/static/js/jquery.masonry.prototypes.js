(function ($, window) {
    Masonry.prototype._layoutItems = function (items, isInstant) {
        if (!items || !items.length) {
            // no items, emit event with empty array
            this.emitEvent('layoutComplete', [ this, items ]);
            return;
        }

        // emit layoutComplete when done
        this._itemsOn(items, 'layout', function onItemsLayout() {
            this.emitEvent('layoutComplete', [ this, items ]);
        });

        // BEGIN WILLET
        this.recent = this.recent || [];
        var queue = [],
            dupes, instagramImg;

        for (var i = 0, len = items.length; i < len; i++) {
            var item = items[i],
                $item = $(item.element);
            // Check to see if we've recently included this instagram image, if we
            // have, we'll want to skip it here.
            instagramImg = $item.find('.instagram :not(.social-buttons) img').prop('src');
            dupes = _.filter(this.recent, function ($elem) {
                var elemImg = $elem.find('.instagram :not(.social-buttons) img').prop('src');
                return (elemImg === instagramImg);
            });

            if (instagramImg && dupes.length !== 0) {
                // remove item from collection
                var index = this.items.indexOf(item);
                this.items.splice(index, 1);
                len -= 1;

                // remove item from DOM
                item.element.parentNode.removeChild(item.element);
                continue;
            }
            // END WILLET
            // get x/y object from method
            var position = this._getItemLayoutPosition(item);
            // enqueue
            position.item = item;
            position.isInstant = isInstant;
            queue.push(position);
        }

        this._processLayoutQueue(queue);
    };

    Masonry.prototype._getItemLayoutPosition = function (item) {
        item.getSize();
        // how many columns does this brick span
        var colSpan = Math.ceil(item.size.outerWidth / this.columnWidth);
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

            if (item.element.className.indexOf('youtube') > -1 && (shortColIndex % 2 !== 0)) {
                continue;
            } else {
                break;
            }
        }

        this.recent = this.recent || [];

        if (item.element.className.indexOf('instagram') > -1) {
            while (this.recent.length > 5) {
                this.recent.shift();
            }

            this.recent.push($(item.element));
        }
        // END WILLET

        // position the brick
        var position = {
            'x': this.columnWidth * shortColIndex,
            'y': minimumY
        };

        // apply setHeight to necessary columns
        var setHeight = position.y + item.size.outerHeight,
            setSpan = this.cols + 1 - colGroup.length;
        for (i = 0; i < setSpan; i++) {
            this.colYs[shortColIndex + i] = setHeight;
        }
        return position;
    };

    // BEGIN WILLET
    Outlayer.Item.prototype._getColumn = function () {
        var colSpan = this.layout._getColSpan(this),
            col = 0;

        while (col * this.layout.columnWidth < this.position.x) {
            ++col;
        }
        return col;
    };

    Masonry.prototype._getColSpan = function (item) {
        item.getSize();
        var colSpan = Math.ceil(item.size.outerWidth / this.columnWidth);
        return Math.min(colSpan, this.cols);
    };

    Masonry.prototype.reload = function () {
        this.reloadItems();
        this.layout();
    };

    // End Willet

})(jQuery, window);