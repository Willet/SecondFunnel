/* global $ */
// jshint -W018

(function () {
    "use strict";
    // IE8 compatibility
    if (!Date.now) {
        Date.now = function () {
            return new Date.getTime();
        };
    }

    var butler = {};

    /**
     * A Task is a job that you give your butler to do so you don't have to
     * deal with the overhead.
     *
     * It will carry out a task over a period of time that depends on priority.
     * If priority is set to 0.5, it will take approximately twice as long.
     *
     * Task accepts a function and an object that includes settings overwrites.
     *
     * A Task will expose to you:
     *    - start: method that starts the task.
     *    - stop: method that stops the task (does not call callbacks).
     *    - addData: method that accepts data and adds it onto the queue. It
     *               also automatically starts the task.
     *    - done: method that adds callbacks that will be called when the queue
     *            is exhausted. (Note: you will have to do this every time your
     *            task stops running.)
     *    - setPriority: method that accepts a number between min and max and
     *                   sets the priority of the task to said number.
     *    - resetPriority: method that resets priority.
     *
     * @param {function} func Function to execute
     * @param {object} options List of options (optional)
     * @constructor
     */
    butler.Task = function (func, options) {
        var self = this,
            initialPriority = 0.8;
        if (!(self instanceof butler.Task)) {
            throw ('Task is a constructor');
        }
        self.running = false;
        // Stores the timer ID of the next call to taskRunner
        self.nextRun = undefined;

        // Stores the timer ID of the next call to checkState
        self.nextCheck = undefined;

        // Average runtime of func
        self.averageRuntime = 0;

        // How many times have we run task
        self.counter = 0;

        // Right now, options stores priority. This will probably change
        self.options = options || {};
        self.queue = [];

        // Function that we will call with data
        self.func = func;

        // Deferred object; allows user to add callbacks that execute when
        // we've exhausted our data
        self.deferred = new $.Deferred();

        // TODO: Move to initializer
        if (options) {
            self.options = $.extend({}, options, true);
        }

        self.checkState = function () {
            if (!(self.queue.length > 0)) {
                self.resolve();
                self.nextCheck = undefined;
            } else {
                self.nextCheck = setTimeout(self.checkState, 20);
            }
        };

        /**
         * getDelay returns what the delay should be for running task, which
         * is then passed to setTimeout. The value it returns depends on
         * average runtime and priority
         * @returns {number}
         */
        self.getDelay = function () {
            var delay =  self.averageRuntime -
                (self.averageRuntime * self.options.priority) +
                8 / self.options.priority;
            return delay;
        };

        /**
         * runTask is called when we want to run func once.
         * Here's how runTask works:
         *     - If there's data in the queue, pop one and send it to
         *       self.func.
         *     - If there's no data in the queue, reset self.running, reset
         *       self.nextRun (timer ID), and resolve the Deferred object.
         *
         * @returns {Task}
         */
        self.runTask = function () {
            //noinspection JSHint
            // If no data
            if (!(self.queue.length > 0)) {
                self.stop();
            } else {
                // console.log('runTask'); //DEBUG
                var start,
                    end,
                    runtime;

                start = Date.now();

                try {
                    // Pop one from our queue, and send it to self.func
                    self.func(self.queue.pop());

                    // Update self.averageRuntime
                    end = Date.now();
                    runtime = end - start;
                    self.counter += 1;
                    self.averageRuntime = (self.averageRuntime + runtime) / self.counter;
                    return self;
                } catch (e) {
                    self.stop();
                    self.deferred.reject(e);
                }
            }
        };

        /**
         * Wrapper for Deferred.resolve. It calls the callbacks provided
         * to the task, and it replaces the Deferred object.
         */
        self.resolve = function () {
            // console.log('resolving'); //DEBUG
            self.deferred.resolve();
            self.deferred = new $.Deferred();
        };

        /**
         * setPriority accepts a number and sets priority to be that number
         * If given an invalid value, it will do one of the following
         * depending on the value:
         *     - Number less than min: set to min
         *     - Number more than max: set to max
         *     - Not a number: set to initialPriority
         *
         * @param priority
         */
        self.setPriority = function (priority) {
            if (typeof priority !== 'number') {
                self.options.priority = initialPriority;
            } else if (priority < 0.05) {
                self.options.priority = 0.05;
            } else if (priority > 1) {
                self.options.priority = 1;
            } else {
                self.options.priority = priority;
            }
        };

        /**
         * resetPriority sets the priority to initialPriority.
         */
        self.resetPriority = function () {
            self.setPriority(initialPriority);
        };

        // TODO move to initializer
        self.resetPriority();

        /**
         * taskRunner glues everything together. It calls runTask and sets
         * the timer for the next run (which is a call to itself).
         */
        self.taskRunner = function () {
            delete console.log;
            console.log('taskRunner');
            if (!(self.queue.length > 0)) {
                self.stop();
            } else if (self.running) {
                self.runTask();
                console.log('yeah');
                var delay = self.getDelay();
                console.log("avg: ", self.averageRuntime, 'priority:', self.options.priority, 'delay:', delay); //DEBUG
                self.nextRun = setTimeout(self.taskRunner, delay);
            }
            if (!self.nextCheck) {
                setTimeout(self.checkState, 20);
            }
        };

        /**
         * starts the task. It's recommended you don't call start unless
         * you know there's data in the queue as calling start will always
         * cause the Deferred object to resolve, so you would lose any
         * callbacks you have added to the task.
         */
        self.start = function () {
            if (self.running) {
                console.warn('Already running');
            } else {
                self.running = true;
                self.taskRunner();
            }
        };

        /**
         * stops the task by doing the following:
         *     - setting self.running to false
         *     - clearing the timer and setting self.nextRun to undefined
         */
        self.stop = function () {
            self.running = false;
            if (self.nextRun) {
                clearTimeout(self.nextRun);
                self.nextRun = undefined;
            }
        };

        /**
         * addData accepts anything as its parameter, and it adds it to the
         * queue of data. IMPORTANT: It also automatically starts the task.
         * @param data
         */
        self.addData = function (data) {
            self.queue.push(data);
            if (!self.running) {
                self.start();
            }
        };


        /**
         * done is a wrapper for Deferred.done. It accepts a function which
         * will then be called when task is done running.
         * @param func
         */
        self.done = function (func) {
            if (self.deferred.state !== 'pending') {
                self.deferred = new $.Deferred();
            }
            self.deferred.done(func);
        };

        self.fail = function (func){
            if (self.deferred.state !== 'pending') {
                self.deferred = new $.Deferred();
            }
            self.deferred.fail(func);
        }
    };

    window.Task = butler.Task;
}());