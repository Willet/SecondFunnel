"use strict";

var api_URL = "http://localhost:8000/api2/";

var result;

var Product = Backbone.Model.extend({
    defaults: {},

    urlRoot: api_URL,

    initialize: function () {
    },

    getCustomURL: function (method) {
        switch (method) {
            case 'read':
                return api_URL + 'page/' + url_slug + '/';
            case 'search':
                return api_URL + 'product/search/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    search: function(searchString) {
        var options = {
            'url': this.getCustomURL('search')
        };
        return Backbone.sync.call(this, 'create', searchString, options);
    }
})

var Page = Backbone.Model.extend({
    defaults: {
        selection: '' ,
        num: ''
    },

    urlRoot: api_URL,

    initialize: function () {
    },

    getCustomURL: function (method) {
        switch (method) {
            case 'read':
                return api_URL + 'page/' + url_slug + '/';
            case 'add':
                return api_URL + 'page/' + url_slug + '/' + method + '/';
            case 'remove':
                return api_URL + 'page/' + url_slug + '/' + method + '/';
        }
    },

    sync: function (method, model, options) {
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());
        return Backbone.sync.call(this, method, model, options);
    },

    add: function (product) {
        var options = {
            'url': this.getCustomURL('add')
        };
        return Backbone.sync.call(this, 'create', product , options);
    },

    remove: function (product) {
        var options = {
            'url': this.getCustomURL('remove')
        };
        return Backbone.sync.call(this, 'create', product , options);
    }
});

var formView = Backbone.View.extend({
    el: $('#allforms'),

    events: {
    	'submit': 'submit'
    },

    initialize: function () {
    },

    submit: function(e) {
    	e.preventDefault();
        var method = '';
        
        if (e.target.id == "add-form")
            method = 'add';
        else
            method = 'remove';

        var selection = e.target.selection.value;
        var num = e.target.id_num.value;

        var page = new Page({
            selection: selection,
            num: num
        });
        if ((method == 'add') || (method == 'remove')) {
            var searchString = new Product();
            if (selection == 'URL')
                searchString.set({url: page.attributes.num});
            if (selection == 'ID')
                searchString.set({url: page.id});
            if (selection == 'SKU')
                searchString.set({url: page.attributes.sku});

            result = searchString.search(searchString);
            result.done(function(){
                if (method == 'add') {
                    result = page.add(page);
                    result.done(function(){
                        $('#add-result').html(JSON.parse(result.responseText).status);
                        $('#remove-result').html("");
                    })
                }
                else{
                    result = page.remove(page);
                    result.done(function(){
                        $('#add-result').html("");
                        $('#remove-result').html(JSON.parse(result.responseText).status);
                    })       
                }
            }).fail(function(){
                if (method == 'add'){
                    $('#add-result').html(JSON.parse(result.responseText));
                    $('#remove-result').html("");
                }
                else{
                    $('#add-result').html("");
                    $('#remove-result').html(JSON.parse(result.responseText));
                }
            })
        }
    },
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(document).ready(function(){
    var Forms = new formView();
    $.ajaxSetup({
        headers: { "X-CSRFToken": getCookie("csrftoken")}
    });
});
