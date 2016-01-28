"use strict";

var api_URL = "http://localhost:8000/api2/";

var result;

var Page = Backbone.Model.extend({
    defaults: {
        //method: "", //Add, remove
        id: '', //ID of the asset
        input: ''
    },

    urlRoot: api_URL,

    initialize: function () {
    },

    getCustomURL: function (method) {
        var methodCase;
        if (_.contains(['add', 'remove'], method))
            methodCase = 'create';
        switch (methodCase) {
            case 'read':
                return api_URL + 'page/' + this.id + '/';
            case 'create':
                return api_URL + 'page/' + this.id + '/' + method + '/';
        }
    },

    sync: function (method, model, options) {
        console.log(method);
        console.log(model);
        console.log(options);
        options || (options = {});
        options.url = this.getCustomURL(method.toLowerCase());

        if (_.contains(['add', 'remove'], method))
            method = 'create';

        console.log("----");
        console.log(method);
        console.log(model);
        console.log(options);
        return Backbone.sync.call(this, method, model, options);
    },

    add: function (product) {
        this.sync('add', product, product.attributes.input);
    },

    remove: function (product) {
        this.sync('remove', product, product.attributes.input);
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
            //method: method,
            id: url_slug,
            input: {
                selection: selection,
                num: num
            }
        });
        page.add(page);
        console.log(page);
        // page.save({}, {
        //     success: function (model, response, options) {
        //         console.log("Saved");
        //     },
        //     error: function (model, xhr, options) {
        //         console.log("error");
        //     }
        // });
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


    // sendRequest: function (attr) {
    //     var url = attr.attributes.apiURL + attr.attributes.asset + "/" + attr.attributes.id + "/" + attr.attributes.method + "/";
    //     var input = attr.attributes.input;
    //     result = jQuery.ajax({
    //         url: url,
    //         type: 'POST',
    //         dataType: 'application/json',
    //         accept: 'application/json',
    //         data: input
    //     });
    //     return result;
    // }



        // result = Request.sendRequest(Request);
        // //readystate 1
        // console.log(result.readyState);
        // console.log(result);
        // $('#add-result').html(result.responseText);