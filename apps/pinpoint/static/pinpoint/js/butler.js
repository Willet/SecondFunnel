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
     * @param {object} opts Object that contains options (optional)
     * @constructor
     */
    window.Task = function (func, opts) {
        if (!(this instanceof Task)) {
            throw ('Task is a constructor');
        }
        if (typeof func !== 'function') {
            throw ('Task needs to receive a function as its first argument');
        }
        
        var self = this,
            running = false,
            options = {},

            // Stores the timer ID of the next call to taskRunner
            nextRun, // Initialized as undefined
            
            // Stores the timer ID of the next call to checkState
            nextCheck, // Initialized as undefined

            // Average runtime of func
            averageRuntime = 0,
            
            // How many times have we run task
            counter = 0,
            
            queue = [],
            
            // Deferred object; allows user to add callbacks that execute when
            // we've exhausted our data
            deferred = new $.Deferred(),
            
            checkState = function () {
                if (!(queue.length > 0)) {
                    resolve();
                    nextCheck = undefined;
                } else {
                    nextCheck = setTimeout(checkState, 20);
                }
            },

            /**
             * getDelay returns what the delay should be for running task, which
             * is then passed to setTimeout. The value it returns depends on
             * average runtime and priority
             * @returns {number}
             */
            getDelay = function () {
                var delay =  averageRuntime -
                    (averageRuntime * options.priority) +
                    1 / options.priority;
                return delay;
            },

            /**
             * runTask is called when we want to run func once.
             * Here's how runTask works:
             *     - If there's data in the queue, pop one and send it to
             *       func.
             *     - If there's no data in the queue, reset running, reset
             *       nextRun (timer ID), and resolve the Deferred object.
             *
             * @returns {Task}
             */
            runTask = function () {
                //noinspection JSHint
                // If no data
                if (!(queue.length > 0)) {
                    self.stop();
                } else {
                    // console.log('runTask'); //DEBUG
                    var start,
                        end,
                        runtime;

                    start = Date.now();

                    try {
                        // Pop one from our queue, and send it to func
                        func(queue.pop());

                        // Update averageRuntime
                        end = Date.now();
                        runtime = end - start;
                        counter += 1;
                        averageRuntime = (averageRuntime + runtime) / counter;
                        return self;
                    } catch (e) {
                        self.stop();
                        deferred.reject(e);
                    }
                }
            },

            /**
             * taskRunner glues everything together. It calls runTask and sets
             * the timer for the next run (which is a call to itself).
             */
            taskRunner = function () {
                delete console.log;
                console.log('taskRunner');
                if (!(queue.length > 0)) {
                    self.stop();
                } else if (running) {
                    runTask();
                    console.log('yeah');
                    var delay = getDelay();
                    console.log("avg: ", averageRuntime, 'priority:', options.priority, 'delay:', delay); //DEBUG
                    nextRun = setTimeout(taskRunner, delay);
                }
                if (!nextCheck) {
                    setTimeout(checkState, 20);
                }
            },
            
            /**
             * Wrapper for Deferred.resolve. It calls the callbacks provided
             * to the task, and it replaces the Deferred object.
             */
            resolve = function () {
                // console.log('resolving'); //DEBUG
                deferred.resolve();
                deferred = new $.Deferred();
            },

            initialize = function () {
                // Make a new copy so external modifications don't change our copy
                options.$.extend({},options,true);
                options.initialPriority = 0.8;
                self.resetPriority();
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
                options.priority = options.initialPriority;
            } else if (priority < 0.05) {
                options.priority = 0.05;
            } else if (priority > 1) {
                options.priority = 1;
            } else {
                options.priority = priority;
            }
        };

        /**
         * resetPriority sets the priority to initialPriority.
         */
        self.resetPriority = function () {
            self.setPriority(options.initialPriority);
        };


        /**
         * starts the task. It's recommended you don't call start unless
         * you know there's data in the queue as calling start will always
         * cause the Deferred object to resolve, so you would lose any
         * callbacks you have added to the task.
         */
        self.start = function () {
            if (running) {
                console.warn('Already running');
            } else {
                running = true;
                taskRunner();
            }
        };

        /**
         * stops the task by doing the following:
         *     - setting running to false
         *     - clearing the timer and setting nextRun to undefined
         */
        self.stop = function () {
            running = false;
            if (nextRun) {
                clearTimeout(nextRun);
                nextRun = undefined;
            }
        };

        /**
         * addData accepts anything as its parameter, and it adds it to the
         * queue of data. IMPORTANT: It also automatically starts the task.
         * @param data
         */
        self.addData = function (data) {
            queue.push(data);
            if (!running) {
                self.start();
            }
        };


        /**
         * done is a wrapper for Deferred.done. It accepts a function which
         * will then be called when task is done running.
         * @param func
         */
        self.done = function (func) {
            if (deferred.state !== 'pending') {
                deferred = new $.Deferred();
            }
            deferred.done(func);
        };

        self.fail = function (func){
            if (deferred.state !== 'pending') {
                deferred = new $.Deferred();
            }
            deferred.fail(func);
        }

        self.always = function (func) {
            if (deferred.state !== 'pending') {
                deferred = new $.Deferred();
            }
            deferred.always(func);
        }
    };
}());