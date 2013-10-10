/* global jQuery, Butler, $ */

(function () {
   "use strict";
   var spliceData,
       addData,
       replaceData,
       Task,
       taskRunner;

   spliceData = function () {
       var count = Math.ceil((this.data.length) * this.priority);
       this.currentTargets = this.data.splice(0, count);
   };

   addData = function (newData) {
       this.data = this.data.concat(newData);
   };

   replaceData = function (newData) {
       this.data = newData;
   };

   Task = function (fn) {
       if (!(this instanceof Task)) {
           throw ('Task is a constructor');
       }
       this.run = function () {
           fn(this.currentTargets);
       };
   };

   taskRunner = function () {
       if (this.working) {

       }
   }

   window.Butler = function (data, fn, priority) {
       if (!(this instanceof window.Butler)) {
           throw ("Butler is a constructor, goddammit!");
       }
       this.data = data;
       this.fn = fn;
       this.priority = 0.1;
       this.spliceData = spliceData;
       this.addData = addData;
       // this.WORKERSUPPORT = Do we support web workers
       return this;
   };
}());