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

var Content = Backbone.Model.extend({
    defaults: {},

    urlRoot: api_URL,

    initialize: function () {
    },

    getCustomURL: function (method) {
        switch (method) {
            case 'read':
                return api_URL + 'page/' + url_slug + '/';
            case 'search':
                return api_URL + 'content/' + method + '/'; 
            case 'upload_cloudinary':
                return api_URL + 'content/' + method + '/'; 
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

    uploadCloudinary: function (URL) {
        var options = {
            'url': this.getCustomURL('upload_cloudinary')
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
        if (e.target.id == "product-add-form")
            method = 'product-add';
        if (e.target.id == "product-remove-form")
            method = 'product-remove';
        if (e.target.id == "content-add-form")
            method = 'content-add';
        if (e.target.id == "content-remove-form")
            method = 'content-remove';

        if ((method == 'product-add') || (method == 'product-remove') || 
            (method == 'content-add') || (method == 'content-remove')) {
            var selection = e.target.selection.value;
            var num = e.target.id_num.value;

            if (method == 'product-add'){
                var priority = e.target.priority.value;
                var category = e.target.category.value;
                page = new Page({
                    type: "product",
                    selection: selection,
                    num: num,
                    priority: priority,
                    category: category
                });
            }
            if (method == 'product-remove'){
                page = new Page({
                    type: "product",
                    selection: selection,
                    num: num,
                });
            }
            if (method == 'content-add'){
                var category = e.target.category.value;
                page = new Page({
                    type: "content",
                    selection: selection,
                    num: num,
                    category: category,
                })
            }
            if (method == 'content-remove'){
                page = new Page({
                    type: "content",
                    selection: selection,
                    num: num,
                });
            }

            if (method.indexOf("content") >= 0){
                contentManage(page, method, selection);
            }
            if (method.indexOf("product") >= 0){              
                productManage(page,method, selection);
            }
        }
    },
});

function productManage(page, method, selection){
    var searchString = new Product();
    if (selection == 'URL')
        searchString.set({url: page.attributes.num});
    if (selection == 'ID')
        searchString.set({id: page.attributes.num});
    if (selection == 'SKU')
        searchString.set({sku: page.attributes.num});

    result = searchString.search(searchString);

    result.done(function(){
        var idLength = JSON.parse(result.responseText).id.length;
        if ((idLength > 0) && (idLength < 2)) {
            page = new Page({
                type: "product",
                ID: JSON.parse(result.responseText).id[0],
            })
            if (method == 'product-add') {
                result = page.add(page);
                result.done(function() {
                    $('#product-add-result').html(JSON.parse(result.responseText).status);
                    $('#product-remove-result').html("");
                })
            }
            if (method == 'product-remove') {
                result = page.remove(page);
                result.done(function(){
                    $('#product-add-result').html("");
                    $('#product-remove-result').html(JSON.parse(result.responseText).status);
                })       
            }
        }
        else{
            if (idLength > 1) {
                if (method == 'product-add') {
                    $('#product-add-result').html("Error: " + JSON.parse(result.responseText).status);
                    $('#product-remove-result').html("");
                }
                if (method == 'product-remove') {
                    $('#product-add-result').html("");
                    $('#product-remove-result').html("Error: " + JSON.parse(result.responseText).status);
                }
            }
            if (idLength < 1) {
                if (method == 'product-add'){
                    $('#product-add-result').html(JSON.parse(result.responseText).status);
                    if ((selection == 'URL') && (JSON.parse(result.responseText).status.indexOf("could not be found") >= 0)) {
                        $('#product-add-result').append(" Scraping...");
                        var scrapeURL = new Product({
                            url: page.attributes.num,
                            page_id: url_slug
                        });
                        result = scrapeURL.scrape(scrapeURL);
                        result.done(function(){
                            $('#product-add-result').append(" " + JSON.parse(result.responseText).status);
                        })
                    }
                    $('#product-remove-result').html("");
                }
                if (method == 'product-remove') {
                    $('#product-add-result').html("");
                    $('#product-remove-result').html(JSON.parse(result.responseText).status);
                }
            }
        }
    })
    return 1;
}

function contentManage(page, method, selection){
    var searchString = new Content();

    if (selection == 'URL')
        searchString.set({url: page.attributes.num});
    if (selection == 'ID')
        searchString.set({id: page.attributes.num});

    result = searchString.search(searchString);
    result.done(function(){
        var idLength = JSON.parse(result.responseText).id.length;
        if ((idLength > 0) && (idLength < 2))  {
            page = new Page({
                type: "content",
                ID: JSON.parse(result.responseText).id[0],
            })
            if (method == 'content-add') {
                result = page.add(page);
                result.done(function() {
                    $('#content-add-result').html(JSON.parse(result.responseText).status);
                    $('#content-remove-result').html("");
                })
            }
            if (method == 'content-remove') {
                result = page.remove(page);
                result.done(function(){
                    $('#content-add-result').html("");
                    $('#content-remove-result').html(JSON.parse(result.responseText).status);
                })       
            }        
        }
        else{
            if (idLength > 1) {
                if (method == 'content-add') {
                    $('#content-add-result').html("Error: " + JSON.parse(result.responseText).status);
                    $('#content-remove-result').html("");
                }
                if (method == 'content-remove') {
                    $('#content-add-result').html("");
                    $('#content-remove-result').html("Error: " + JSON.parse(result.responseText).status);
                }
            }
            if (idLength < 1) {
                if (method == 'content-add'){
                    $('#content-add-result').html(JSON.parse(result.responseText).status);
                    if ((selection == 'URL') && (JSON.parse(result.responseText).status.indexOf("could not be found") >= 0)) {
                        $('#content-add-result').append(" Uploading to cloudinary...");
                        var uploadURL = new Product({
                            url: page.attributes.num,
                        });
                        result = uploadURL.uploadCloudinary(uploadURL);
                        result.done(function(){
                            $('#content-add-result').append(" " + JSON.parse(result.responseText).status);
                        })
                    }
                    $('#content-remove-result').html("");
                }
                if (method == 'content-remove') {
                    $('#content-add-result').html("");
                    $('#content-remove-result').html(JSON.parse(result.responseText).status);
                }
            }
        }
    })
    return 1;
}

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
