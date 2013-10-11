/* global $ */

(function () {
    "use strict";
    var butler = {};

    // data is optional
    butler.Task = function (func, data, options) {
        var self = this;
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

            if (data) {
                self.queue.push(data);
            }
            if (options) {
                self.options = $.extend({}, options, true);
            }

            self.runTask = function () {
                //noinspection JSHint
                if (!(self.queue.length > 0)) {
                    if (self.running) {
                        self.running = false;
                        self.nextRun = undefined;
                    }
                } else {
                    var start,
                        end,
                        runtime;
                    start = new Date().getTime();
                    self.func(self.queue.shift());
                    end = new Date().getTime();
                    runtime = end - start;
                    self.counter += 1;
                    self.averageRuntime = (self.averageRuntime + runtime) / self.counter;
                    return self;
                }
            };

            self.setPriority = function (priority) {
                if (priority < 0.1) {
                    self.options.priority = 0.1;
                }
                if (priority > 1) {
                    self.options.priority = 1;
                } else {
                    self.options.priority = 1;
                }
            };

            self.setPriority(0.5);

            self.taskRunner = function () {
                self.runTask();
                if (self.running) {
                    var delay = (self.averageRuntime / self.priority) - (1 / self.priority);
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
            };

            self.addData = function (data) {
                self.queue.push(data);
                self.start();
            };

        }
    };

    window.Task = butler.Task;
}());