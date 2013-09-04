/*global Masonry, _, console, $, jQuery */
/* Flexibility 2.6:
   It should be possible to define simple rules for how tiles can be placed, or sized.

   Implementation Concerns:
       - May not be compatible with future iterations of Masonry.
       - Have to extend Masonry to allow layout logic control which divs can be placed near each
         other; for this purpose, we'll assume two divs are the same if they have the same type;
         so the same class name besides the selector).
*/

// Helper functions
function getRectangle(elem) {
    // Get the bounding rectangle if it exists
    var rect = elem;
    if (elem.getBoundingClientRect) {
        // Include the margin as BoundingClientRect does not
        rect = elem.getBoundingClientRect();
        _.each(["left", "right", "top", "bottom"], function (or) {
            rect[or] += $(elem).css('margin-' + or);
        });
    }
    return rect;
}

function near(elem1, elem2, distance) {
    var rect1 = getRectangle(elem1),
        rect2 = getRectangle(elem2);
    // TODO: Where is this 15 coming from ?
    distance += 15;

    // Test if they are within distance
    return true;
}

Masonry.prototype.__create = Masonry.prototype._create;
Masonry.prototype._create = function () {
    // Call the actual create method
    this.__create();
    // Check for filters
    if (this.options.filters) {
        var _filters = [];
        for (var i = 0; i < this.options.filters.length; ++i) {
            var _filter = this.options.filters[i];
            if (this._filters[_filter]) {
                _filters.push(this._filters[_filter]);
            }
        }
        this.options.filters = _filters;
    }
};

Masonry.prototype._filters = {
    'sameClass': function (elem1, elem2) {
        // Returns true if two elements share the same class.
        var classes = elem1.className.replace(this.options.itemSelector, "");
        classes = classes.split(" ");
        for (var i = 0; i < classes.length; ++i) {
            var cls = classes[i];
            if ($(elem2).hasClass(cls)) {
                return false;
            }
        }
        return true;
    }
};

Masonry.prototype._getColSpan = function (item) {
    var colSpan;
    item.getSize();
    colSpan = Math.ceil(item.size.outerWidth / this.columnWidth);
    return Math.min(colSpan, this.cols);
};

Masonry.prototype._layoutItems = function (items, isInstant) {
    if (!items || !items.length) {
        // no items, emit event with empty array
        this.emitEvent('layoutComplete', [this, items]);
        return;
    }

    // emit layoutComplete when done
    this._itemsOn(items, 'layout', function onItemsLayout() {
        this.emitEvent('layoutComplete', [this, items]);
    });

    // Keep track of the recently laid out items
    this.recent = this.recent || [];

    var queue = [], i,
    // used for determing changes and/or exit conditions
        ignoreFail = false, changed = true;

    while (items.length > 0) {
        // Changed becomes false as we've yet to go through
        // the items
        changed = false;
        for (i = 0; i < items.length; ++i) {
            var item = items[i];
            // get x/y object from method
            var position = this._getItemLayoutPosition(item, ignoreFail);
            if (position) {
                // enqueue
                position.item = item;
                position.isInstant = isInstant;
                changed = true;
                this.recent.push(item);
                items.splice(i, 1);
                queue.push(position);
                --i;
            }
        }
        if (changed == false) {
            ignoreFail = true;
        }
    }

    this._processLayoutQueue(queue);
};


Masonry.prototype._getItemLayoutPosition = function (item, ignoreFail) {
    // how many columns does this brick span
    var colSpan = this._getColSpan(item),
        i, y;

    // Determine the column group
    var colGroup = this._getColGroup(colSpan);
    // get the minimum Y value(s) from the columns.
    var minimumYs = _.clone(colGroup).sort(function (a, b) {
            return a > b;
        }),
        minimumY = _.indexOf(colGroup, minimumYs[0]);

    for (i = 0; i < minimumYs.length && !ignoreFail; ++i) {
        var failed = false,
            index = _.indexOf(colGroup, minimumYs[i]);

        for (var k = 0; k < this.recent.length && !failed; ++k) {
            var elem = this.recent[k].element,
                left = this.columnWidth * index,
                pos = {
                    'left': left,
                    'right': left + item.size.outerWidth,
                    'top': colGroup[index],
                    'bottom': colGroup[index] + item.size.outerHeight
                };
            // If these two items are near each other, apply the filters
            // to check if the element is okay.
            if (near(pos, elem, this.gutter)) {
                // Apply the filters and check for failure
                _.each(this.options.filter, function (filter) {
                    failed = failed || !filter(elem, item.element);
                });
            }
        }
        // Break successfully if not failed, this is the 
        // column to use.
        if (!failed) {
            minimumY = index;
            break;
        }
    }

    if (minimumYs.length === 0 && !ignoreFail) {
        // This item failed to pass the rules
        return undefined;
    }

    var shortColIndex = minimumY,
        shortColY = colGroup[shortColIndex];

    // position the brick
    var position = {
        x: this.columnWidth * shortColIndex,
        y: shortColY
    };

    // apply setHeight to necessary columns
    var setHeight = shortColY + item.size.outerHeight,
        setSpan = this.cols + 1 - colGroup.length;
    for (i = 0; i < setSpan; ++i) {
        this.colYs[ shortColIndex + i ] = setHeight;
    }
    return position;
};
