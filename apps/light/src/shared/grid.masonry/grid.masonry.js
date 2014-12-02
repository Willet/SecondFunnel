/*!
 * Grid Masonry v0.0.1
 *
 * Most Masonry features, such as stamp's, layout right-to-left, layout bottom-to-top, etc remain untested
 *
 * extended from:
 *
 * Masonry v3.1.5
 * Cascading grid layout library
 * http://masonry.desandro.com
 * MIT License
 * by David DeSandro
 */
//
"use strict"
var Outlayer = require('outlayer');
var getSize = require('get-size');
var _ = require('underscore');
var $ = require('jquery');

// -------------------------- gridMasonryDefinition -------------------------- //
// create an Outlayer layout class
var GridMasonry = Outlayer.create('masonry');

GridMasonry.prototype._resetLayout = function() {
  this.getSize();
  this._getMeasurement( 'columnWidth', 'outerWidth' );
  this['rowHeight'] = this.columnWidth / (this.option.tileAspectRatio ? this.option.tileAspectRatio : 1);
  this._getMeasurement( 'gutter', 'outerWidth' );
  this.measureColumns();

  // reset column Y
  var i = this.cols;
  this.colYs = [];
  while (i--) {
    this.colYs.push( 0 );
  }

  this.maxY = 0;
  this._currentRowY = 0;
};

GridMasonry.prototype.measureColumns = function() {
  // set this.cols as the calculated number of columns
  this.getContainerWidth();
  // if columnWidth is 0, default to outerWidth of first item
  if ( !this.columnWidth ) {
    var firstItem = this.items[0];
    var firstItemElem = firstItem && firstItem.element;
    // columnWidth fall back to item of first element
    this.columnWidth = firstItemElem && getSize( firstItemElem ).outerWidth ||
      // if first elem has no width, default to size of container
      this.containerWidth;
  }

  this.columnWidth += this.gutter;

  this.cols = Math.floor( ( this.containerWidth + this.gutter ) / this.columnWidth );
  this.cols = Math.max( this.cols, 1 );
};

GridMasonry.prototype.getContainerWidth = function() {
  // container is parent if fit width
  var container = this.options.isFitWidth ? this.element.parentNode : this.element;
  // check that this.size and size are there
  // IE8 triggers resize on body size change, so they might not be
  var size = getSize( container );
  this.containerWidth = size && size.innerWidth;
};

GridMasonry.prototype._getNextRowY = function () {
  // finds the lowest height were all tiles on that row have a height within the variance
  var colYs = this.colYs,
      rowHeight = this.rowHeight,
      currentRowY = this._currentRowY,
      heightVariance = this.options.heightVariance || 0.2; // default: +/- 10%
  function removeExcessCols (cleanArr, colY) {
    // If height is within variance, add it to array
    if ( (Math.abs(colY-rowHeight-currentRowY)) < (heightVariance*rowHeight) ) {
      cleanArr.push(colY);
    }
    return cleanArr;
  }
  var boundedColYs = _.reduce( colYs, removeExcessCols, [] );
  
  if (boundedColYs.length < 1) {
    // No tiles are within one row height
    // Find the next possible row height, find the tiles within variance of that
    // and then choose the height of lowest tile
    currentRowY = Math.min.apply(null, colYs) - rowHeight; // Have to correct for subtracting it later
    boundedColYs = _.reduce( colYs, removeExcessCols, [] );
  }
  return Math.max.apply(null, boundedColYs);
};

GridMasonry.prototype._updateCurrentRow = function( newY ) {
  // Useful for discovering errors in the grid
  // Replace any assignment to _currentRowY with this function and add this css:
  // .gridmasonry.line {
  //     width: 100%;
  //     border-top: 1px solid red;
  //     padding: 0;
  //     margin: 0;
  //     position: absolute;
  //     left: 0;
  // }
  if (newY > this._currentRowY) {
    this._currentRowY = newY;
    $(document.createElement('div')).addClass('gridmasonry line').css({ 'top': newY+$('.discovery-area').offset().top }).appendTo(document.body);
  } else if (newY === 0) {
    $('.gridmasonry.line').remove();
    $(document.createElement('div')).addClass('gridmasonry line').css({ 'top': newY+$('.discovery-area').offset().top }).appendTo(document.body);
  }
};

GridMasonry.prototype._getItemLayoutPosition = function( item ) {
  // Assumption: 
  //    - tiles are within X% height of each other (or a multiple of height), roughly creating a grid
  // Recalculate currentRowY
  if ( !this._currentRowY ) {
    this._currentRowY = 0;
  }

  item.getSize();
  // how many columns does this brick span
  var remainder = item.size.outerWidth % this.columnWidth;
  var mathMethod = remainder && remainder < 1 ? 'round' : 'ceil';
  // round if off by 1 pixel, otherwise use ceil
  var colSpan = Math[ mathMethod ]( item.size.outerWidth / this.columnWidth );
  colSpan = Math.min( colSpan, this.cols );

  var colGroup = this._getColGroup( colSpan );
  var _this = this;

  
  // Determine if there are empty spots on our current grid row by checking if the column already exceeds it
  function findEmptySpot (colY) {
    return ((colY - _this._currentRowY) > 0);
  }
  var noEmptyCols = Math.min.apply( null, _.map(this.colYs, findEmptySpot ) );
  if (noEmptyCols) {
    // start new row
    // this._updateCurrentRow( this._getNextRowY() ); // show grid lines
    this._currentRowY = this._getNextRowY();
  }

  // get the left-most column that has a height less than or equal to the row
  function findColOnCurrentRow(arr, y) {
    if (y <= _this._currentRowY) {
      arr.push(y);
    }
    return arr;
  }
  var colGroup = this._getColGroup( colSpan );
  var colGroupOnCurrentRow = _.reduce( colGroup, findColOnCurrentRow, [] );
  
  if (colGroupOnCurrentRow.length) {
    // Tile fits in empty spot on current row
    var shortColIndex = _.indexOf( colGroup, colGroupOnCurrentRow[0] );
    
    // position the brick
    var position = {
      x: this.columnWidth * shortColIndex,
      y: this._currentRowY
    };

    // apply setHeight to necessary columns
    var setHeight = this._currentRowY + item.size.outerHeight;
    var setSpan = this.cols + 1 - colGroup.length;
    for ( var i = 0; i < setSpan; i++ ) {
      this.colYs[ shortColIndex + i ] = setHeight;
    }
    return position; 

  } else {
    // Tile does not fit in empty spot (tile width > columns available)
    return false; // 'try again later'
  }
};

/**
 * @param {Number} colSpan - number of columns the element spans
 * @returns {Array} colGroup
 */
GridMasonry.prototype._getColGroup = function( colSpan ) {
  if ( colSpan < 2 ) {
    // if brick spans only one column, use all the column Ys
    return this.colYs;
  }

  var colGroup = [];
  // how many different places could this brick fit horizontally
  var groupCount = this.cols + 1 - colSpan;
  // for each group potential horizontal position
  for ( var i = 0; i < groupCount; i++ ) {
    // make an array of colY values for that one group
    var groupColYs = this.colYs.slice( i, i + colSpan );
    // and get the max value of the array
    colGroup[i] = Math.max.apply( Math, groupColYs );
  }
  return colGroup;
};

GridMasonry.prototype.stashItem = function( item ) {
  if (!this._delayedQueue ) {
    this._delayedQueue = [];
  }
  $(item.element).addClass('gridmasonry purple');
  item.hide();
  item.isIgnored = true;
  this._delayedQueue.push( item );
};

GridMasonry.prototype.unstashItem = function() {
  if ( this._delayedQueue && this._delayedQueue.length ) {
    var delayedItem = this._delayedQueue.shift();
    if ( delayedItem ) {
      delete delayedItem.isIgnored;
      delayedItem.reveal();
      return delayedItem;
    }
  }
  return undefined;
};

GridMasonry.prototype._layoutItems = function( items, isInstant ) {
  var _this = this;

  if ( !items || !items.length ) {
    // No items, emit with empty array
    _this.emitEvent( 'layoutComplete', [ _this, items ] );
    return;
  }

  var queue = [];

  function queueItem(item) {
    var position = _this._getItemLayoutPosition( item );
    if (!position) {
      // store item to attempt after next time
      _this.stashItem( item );
      
    } else {
      console.log('got item position x,y '+position.x+','+position.y)
      // enqueue
      position.item = item;
      position.isInstant = isInstant || item.isLayoutInstant;
      queue.push( position );

      // try placing a delayed item
      var delayedItem = _this.unstashItem();
      if (delayedItem) {
        queueItem( delayedItem );
      }
    }
  }

  for ( var i=0, len = items.length; i < len; i++ ) {
    // get x/y object from method
    queueItem( items[i] );
  }

  // get array of queued items
  var queuedItems = _.map( queue, function (position){ return position.item; });

  // emit layoutComplete when queued items are placed
  this._itemsOn( queuedItems, 'layout', function (){  
    _this.emitEvent( 'layoutComplete', [ _this, queuedItems ] ); console.log('layoutComplete');
  });

  this._processLayoutQueue( queue );
};

GridMasonry.prototype._manageStamp = function( stamp ) {
  var stampSize = getSize( stamp );
  var offset = this._getElementOffset( stamp );
  // get the columns that this stamp affects
  var firstX = this.options.isOriginLeft ? offset.left : offset.right;
  var lastX = firstX + stampSize.outerWidth;
  var firstCol = Math.floor( firstX / this.columnWidth );
  firstCol = Math.max( 0, firstCol );
  var lastCol = Math.floor( lastX / this.columnWidth );
  // lastCol should not go over if multiple of columnWidth #425
  lastCol -= lastX % this.columnWidth ? 0 : 1;
  lastCol = Math.min( this.cols - 1, lastCol );
  // set colYs to bottom of the stamp
  var stampMaxY = ( this.options.isOriginTop ? offset.top : offset.bottom ) +
    stampSize.outerHeight;
  for ( var i = firstCol; i <= lastCol; i++ ) {
    this.colYs[i] = Math.max( stampMaxY, this.colYs[i] );
  }
};

GridMasonry.prototype._getContainerSize = function() {
  this.maxY = Math.max.apply( Math, this.colYs );
  var size = {
    height: this.maxY
  };

  if ( this.options.isFitWidth ) {
    size.width = this._getContainerFitWidth();
  }

  return size;
};

GridMasonry.prototype._getContainerFitWidth = function() {
  var unusedCols = 0;
  // count unused columns
  var i = this.cols;
  while ( --i ) {
    if ( this.colYs[i] !== 0 ) {
      break;
    }
    unusedCols++;
  }
  // fit container to columns that have been used
  return ( this.cols - unusedCols ) * this.columnWidth - this.gutter;
};

GridMasonry.prototype.needsResizeLayout = function() {
  var previousWidth = this.containerWidth;
  this.getContainerWidth();
  return previousWidth !== this.containerWidth;
};

GridMasonry.prototype.reveal = function( items ) {
  var len = items && items.length;
  if ( !len ) {
    return;
  }
  for ( var i=0; i < len; i++ ) {
    var item = items[i];
    // Use ignored to not show elements that weren't placed
    if (!item.isIgnored) {
      item.reveal();
    }
  }
};

module.exports = GridMasonry;
