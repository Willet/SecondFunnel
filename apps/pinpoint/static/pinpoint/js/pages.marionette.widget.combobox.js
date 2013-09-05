/*global $, _, SecondFunnel, sizeImage*/

// experimental combobox widget. usable, but not pretty
SecondFunnel.utils.addWidget(
    'combobox',  // name (must be unique)
    'div.combobox-enabled',  // selector (scoped!)
    function (view, $el, option) {
        var data = view.model,
            related = view.model.get('related-products')[0],
            actualTile = $el.parents('.tile'),
            boundingBox = $('<div class="row" />'),
            left = $('<div class="col-xs-12 col-md-6" />'),
            right = $('<div class="col-xs-12 col-md-6" />'),
            product = $('<div class="caption">' + related.title + '</div>').prepend($('<img />', {
                'src': related.image
            }));
        actualTile.addClass('wide');  // it ought to do more, but not right now

        right.prepend(product);
        actualTile.find('img.focus').appendTo(left);
        actualTile.contents().appendTo(right);
        boundingBox.append(left).append(right);

        boundingBox.appendTo(actualTile);
    }
);