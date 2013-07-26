var Willet = Willet || {};

// Willet's very own mediator
Willet.mediator = (function (me) {
    // example on: Willet.mediator.on('eventName', function (params) {
    //     alert(params);
    // });
    // example fire: Willet.mediator.fire('eventName', 'hello world');
    "use strict";

    // you shouldn't need to manipulate this object, but you can if you want.
    me.hooks = me.hooks || {
        /* event1: [
            [func, params],
            [func, params],
            [func, params],
            ...
        ], event2: [
            ...
        ]
        */
    };

    // get a callback for a given event.
    // it allows other applications to call our registered events.
    me.callback = me.callback || function (event) {
        return function (params) {
            me.fire(event, params);
        };
    };

    // trigger an event. fire all functions assigned to that event.
    // params is optional.
    me.fire = me.fire || function (event, params) {
        var i, cb;

        if (!me.hooks[event]) {
            var hook;
            for (i = 0; i < me.hooks.length; i++) {
                // look for moduleName.functionName auto-triggers.
                var dotIndex = hook.indexOf('.');
                hook = me.hooks[i];
                if (dotIndex > 0) {  // has a dot and (moduleName.length > 0)
                    if (Willet[hook.substr(0, dotIndex)]) {  // check for module
                        cb = Willet[hook.substr(0, dotIndex)][hook.substr(dotIndex + 1)];
                        if (cb) {  // check for function
                            break;
                        }
                    }
                }
            }
            if (cb) {
                // a list of [ function, [parameters] ]
                me.hooks[event] = [[cb, []]];
            } else {
                if (console && console.warn) {
                    console.warn('Calling ' + event + ' has no effect.');
                }
                return me; // no functions registered with this event.
            }
        }
        // console.log(me.hooks[event].length + ' events to run');
        for (i = 0; i < me.hooks[event].length; i++) {
            try {
                params = params || me.hooks[event][i][1] || [];

                // if params given as a non-list, auto-correct it for .apply()
                if (!params instanceof Array) {
                    params = [params];
                }

                // the following shitty line executes one of the callback
                // functions for this event.
                me.hooks[event][i][0].apply(this, params);

                // if (event !== 'log') {
                //     me.fire('log', 'called event: ' + event);
                // }
            } catch (err) {
                // continue running other hooks.
                if (event !== 'error') {  // prevent stack overflow (fo cereals)
                    me.fire('error', 'failed to call an event: ' + err);
                }
            }
        }

        // execute auto-registered functions, if any.
        try {
            me.autoFire(event, params);
        } catch (err) {
            if (event !== 'log') {
                me.fire('log', 'failed to autoCall an event: ' + err);
            }
        }
        return me;
    };

    me.autoFire = me.autoFire || function (event, params) {
        // http://addyosmani.com/largescalejavascript/
        // automatic firing of non-subscribed functions inside all modules.
        // functions can be autofired...
        // e.g. autoEventCall will be called when "eventCall" is fired.

        // auto-camel-case the function that we will be calling.
        var funcName = 'auto' + event[0].toUpperCase() + event.substr(1),
            module;
        for (module in Willet) {
            if (Willet.hasOwnProperty(module)) {
                if (Willet[module][funcName]) {
                    Willet[module][funcName].apply(this, params);
                }
            }
        }
    };

    me.getResult = me.getResult || function (event, params) {
        // call the last function registered to an event.
        // returns the function return (main reason why you'd use getResult())
        // params is optional.
        var eventHooks = me.hooks[event] || [];

        try {
            var lastFunction = eventHooks[eventHooks.length - 1][0],
                lastParams = eventHooks[eventHooks.length - 1][1];

            return lastFunction(params || lastParams);
        } catch (e) {
            // oh well
        }
    };

    // subscribing to an event - fire a function when it happens. (FIFO)
    // params is optional.
    me.on = me.on || function (event, func, params) {
        var hooks = me.hooks;
        hooks[event] = hooks[event] || [];
        hooks[event].push([func, params]);
        return me;
    };
    // aliases. just because they are there and they make sense,
    // it doesn't mean you *should* use all of them.
    // try to stick to one of them in each project.
    me.listen = me.register = me.on;

    // unregistering an event.
    // name of the event is required.
    me.off = me.off || function (event) {
        delete me.hooks[event];
        return me;
    };
    me.unlisten = me.unregister = me.on;

    // replace all previous hooks with this single one.
    // params is optional.
    me.replace = me.replace || function (event, func, params) {
        me.off(event).on(event, func, params);
        return me;
    };

    return me;  // insecure augmentation (doesn't matter)
}(Willet.mediator || {}));