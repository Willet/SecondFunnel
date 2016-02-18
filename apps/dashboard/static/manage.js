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
});

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
            case 'scrape':
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

    scrape: function (URL) {
        var options = {
            'url': this.getCustomURL('scrape')
        };
        return Backbone.sync.call(this, 'create', URL, options);
    }
});

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

function productManage(page, method, selection){
    var searchString = new Product();
    if (selection == 'URL')
        searchString.set({url: page.attributes.num});
    if (selection == 'ID')
        searchString.set({id: page.attributes.num});
    if (selection == 'SKU')
        searchString.set({sku: page.attributes.num});

    result = searchString.search(searchString);
    result.always(function(){
        var idLength = JSON.parse(result.responseText).ids.length;
        if (idLength == 1) {
            page = new Page({
                type: "product",
                id: JSON.parse(result.responseText).ids[0],
            })
            if (method == 'product-add') {
                result = page.add(page);
                result.always(function() {
                    $('#product-add-result').html(JSON.parse(result.responseText).status);
                    $('#product-remove-result').html("");
                })
            }
            if (method == 'product-remove') {
                result = page.remove(page);
                result.always(function(){
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
                        result.always(function(){
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
    result.always(function(){
        var idLength = JSON.parse(result.responseText).ids.length;
        if (idLength == 1) {
            page = new Page({
                type: "content",
                id: JSON.parse(result.responseText).ids[0],
            })
            if (method == 'content-add') {
                result = page.add(page);
                result.always(function() {
                    $('#content-add-result').html(JSON.parse(result.responseText).status);
                    $('#content-remove-result').html("");
                })
            }
            if (method == 'content-remove') {
                result = page.remove(page);
                result.always(function(){
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
                        $('#content-add-result').append(" Scraping...");
                        var uploadURL = new Product({
                            url: page.attributes.num,
                        });
                        result = uploadURL.scrape(uploadURL);
                        result.always(function(){
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

var addProductModel = Backbone.Model.extend({
    schema: {
        selection: { title: 'Selection', type: 'Select', options: ['URL', 'SKU', 'ID'] },
        num:       { title: 'Number', type: 'Text' },
        priority:  { title: 'Priority', type: 'Text' },
        category:  { title: 'Category', type: 'Text' },
    },
});

var removeProductModel = Backbone.Model.extend({
    schema: {
        selection: { title: 'Selection', type: 'Select', options: ['URL', 'SKU', 'ID'] },
        num:       { title: 'Number', type: 'Text' },
    },
});

var addContentModel = Backbone.Model.extend({
    schema: {
        selection: { title: 'Selection', type: 'Select', options: ['URL', 'ID'] },
        num:       { title: 'Number', type: 'Text' },
        category:  { title: 'Category', type: 'Text' },
    },
});

var removeContentModel = Backbone.Model.extend({
    schema: {
        selection: { title: 'Selection', type: 'Select', options: ['URL', 'ID'] },
        num:       { title: 'Number', type: 'Text' },
    },
});

var addProduct = new addProductModel();
var removeProduct = new removeProductModel();
var addContent = new addContentModel();
var removeContent = new removeContentModel();

var addProductForm = new Backbone.Form({
    model: addProduct,
}).render();

var removeProductForm = new Backbone.Form({
    model: removeProduct,
}).render();

var addContentForm = new Backbone.Form({
    model: addContent,
}).render();

var removeContentForm = new Backbone.Form({
    model: removeContent,
}).render();

$('#addProductDiv').append(addProductForm.el);
$('#removeProductDiv').append(removeProductForm.el);
$('#addContentDiv').append(addContentForm.el);
$('#removeContentDiv').append(removeContentForm.el);

$('#product-add-button').click(function(){
    addProductForm.commit();
    
    var selection = addProduct.attributes.selection;
    var num = addProduct.attributes.num;
    var priority = addProduct.attributes.priority;
    var category = addProduct.attributes.category;

    var page = new Page({
        type: "product",
        selection: selection,
        num: num,
        priority: priority,
        category: category
    });
    productManage(page,'product-add', selection);
})

$('#product-remove-button').click(function(){
    removeProductForm.commit();

    var selection = removeProduct.attributes.selection;
    var num = removeProduct.attributes.num;

    var page = new Page({
        type: "product",
        selection: selection,
        num: num,
    });

    productManage(page,'product-remove', selection);
})

$('#content-add-button').click(function(){
    addContentForm.commit();

    var selection = addContent.attributes.selection;
    var num = addContent.attributes.num;
    var category = addContent.attributes.category;

    var page = new Page({
        type: "content",
        selection: selection,
        num: num,
        category: category
    });

    contentManage(page,'content-add', selection);
})

$('#content-remove-button').click(function(){
    removeContentForm.commit();

    var selection = removeContent.attributes.selection;
    var num = removeContent.attributes.num;

    var page = new Page({
        type: "content",
        selection: selection,
        num: num,
    });

    contentManage(page,'content-remove', selection);
})

// Used to get CSRF Token Cookie so django will allow us to use do API calls
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
    //var Forms = new formView();
    $.ajaxSetup({
        headers: { "X-CSRFToken": getCookie("csrftoken")}
    });
});