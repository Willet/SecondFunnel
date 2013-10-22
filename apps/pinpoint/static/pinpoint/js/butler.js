/* global $ */
// jshint -W018

(function () {
    "use strict";
    var butler = {};

    // data is optional
    butler.Task = function (func, options) {
        var self = this,
            initialPriority = 1;
        if (!(self instanceof butler.Task)) {
            throw ('Task is a constructor');
        } else {
            self.running = false;
            self.nextRun = undefined;
            self.averageRuntime = 0;
            self.counter = 0;
            self.options = options || {};
            self.queue = [];
            self.func = func;
            self.doneCallBacks = [];
            self.deferred = new $.Deferred();

            if (options) {
                self.options = $.extend({}, options, true);
            }

            self.runTask = function () {
                //noinspection JSHint
                if (!(self.queue.length > 0)) {
                    // console.log('resolve'); //DEBUG
                    self.deferred.resolve();
                    self.running = false;
                    self.nextRun = undefined;
                } else {
                    // console.log('runTask'); //DEBUG
                    var start,
                        end,
                        runtime;
                    start = Date.now();
                    self.func(self.queue.pop());
                    end = Date.now();
                    runtime = end - start;
                    self.counter += 1;
                    self.averageRuntime = (self.averageRuntime + runtime) / self.counter;
                    return self;
                }
            };

            self.resolve = function () {
                // console.log('resolving'); //DEBUG
                self.deferred.resolve();
                self.deferred = new $.Deferred();
            };

            self.setPriority = function (priority) {
                if (priority < 0.05) {
                    self.options.priority = 0.05;
                }
                if (priority > 1) {
                    self.options.priority = 1;
                } else {
                    self.options.priority = priority;
                }
            };

            self.resetPriority = function () {
                self.setPriority(initialPriority);
            };

            self.resetPriority();

            self.taskRunner = function () {
                self.runTask();
                if (!(self.queue.length > 0)) {
                    self.resolve();
                }
                if (self.running) {
                    var delay = (self.averageRuntime / self.priority) - (1 / self.priority);
                    // console.log(delay); //DEBUG
                    self.nextRun = setTimeout(self.taskRunner, delay);
                }
           };

            self.start = function () {
                if (self.running) {
                    console.warn('Already running');
                } else {
                    self.running = true;
                    self.taskRunner();
                }
            };

            self.stop = function () {
                self.running = false;
                if (self.nextRun) {
                    clearTimeout(self.nextRun);
                    self.nextRun = undefined;
                }
                self.resolve();
            };

            self.addData = function (data) {
                self.queue.push(data);
                if (!self.running) {
                    self.start();
                }
            };


            // Wrapper for deferred.done
            self.done = function (func) {
                if (self.deferred.state !== 'pending') {
                    self.deferred = new $.Deferred();
                }
                self.deferred.done(func);
            };
        }
    };

    window.Task = butler.Task;
}());