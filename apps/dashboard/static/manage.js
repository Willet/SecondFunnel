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
                return api_URL + 'product/' + method + '/'; 
            case 'scrape':
                return api_URL + 'product/' + method + '/'; 
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
    },

    scrape: function (URL) {
        var options = {
            'url': this.getCustomURL('scrape')
        };
        return Backbone.sync.call(this, 'create', URL, options);
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
        var page = '';
        if (e.target.id == "add-form")
            method = 'add';
        else
            method = 'remove';

        if ((method == 'add') || (method == 'remove')) {
            var selection = e.target.selection.value;
            var num = e.target.id_num.value;
            
            if (method == 'add'){
                var priority = e.target.priority.value;
                var category = e.target.category.value;
                page = new Page({
                    selection: selection,
                    num: num,
                    priority: priority,
                    category: category
                });
            }
            else{
                page = new Page({
                    selection: selection,
                    num: num,
                });
            }

            var searchString = new Product();
            if (selection == 'URL')
                searchString.set({url: page.attributes.num});
            if (selection == 'ID')
                searchString.set({id: page.attributes.num});
            if (selection == 'SKU')
                searchString.set({sku: page.attributes.num});

            result = searchString.search(searchString);

            result.done(function(){
                if (JSON.parse(result.responseText).status.indexOf("has been found") >= 0) {
                    if (method == 'add') {
                        result = page.add(page);
                        result.done(function() {
                            $('#add-result').html(JSON.parse(result.responseText).status);
                            $('#remove-result').html("");
                        })
                    }
                    else {
                        result = page.remove(page);
                        result.done(function(){
                            $('#add-result').html("");
                            $('#remove-result').html(JSON.parse(result.responseText).status);
                        })       
                    }
                }
                else{
                    if (JSON.parse(result.responseText).status.indexOf("Multiple") >= 0) {
                        if (method == 'add') {
                            $('#add-result').html("Error: " + JSON.parse(result.responseText).status);
                            $('#remove-result').html("");
                        }
                        else {
                            $('#add-result').html("");
                            $('#remove-result').html("Error: " + JSON.parse(result.responseText).status);
                        }
                    }
                    else{
                        if (method == 'add'){
                            $('#add-result').html(JSON.parse(result.responseText).status);
                            if (selection == 'URL'){
                                $('#add-result').append(" Scraping...");
                                var scrapeURL = new Product({
                                    url: page.attributes.num,
                                    page_id: url_slug
                                });
                                result = scrapeURL.scrape(scrapeURL);
                                result.done(function(){
                                    $('#add-result').append(" " + JSON.parse(result.responseText).status);
                                })
                            }
                            $('#remove-result').html("");
                        }
                        else{
                            $('#add-result').html("");
                            $('#remove-result').html(JSON.parse(result.responseText).status);
                        }
                    }
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
