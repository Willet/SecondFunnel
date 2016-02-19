"use strict";

var api_URL = "http://localhost:8000/api2/";

var result;

var Tile = Backbone.Model.extend({
    defaults: {},

    urlRoot: api_URL,

    initialize: function () {
    },

    getCustomURL: function (method) {
        switch (method) {
            case 'edit_priority':
                return api_URL + 'tile/edit_single_priority/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    changePriority: function(input) {
        var options = {
            'url': this.getCustomURL('edit_priority')
        };
        return Backbone.sync.call(this, 'create', input, options);
    },
});

function editTile(tile_id, prio){
    var tile = new Tile({
        tile_id: tile_id,
        priority: prio,
    })
    result = tile.changePriority(tile);
    result.always(function() {
        $('#result').html(JSON.parse(result.responseText).status);
    })
}

function checkPrio(tile_id){
    if (document.getElementById('result').value != "")
    	window.location.reload();
}

$(function(){
	$('#all-tiles').sortable();
})