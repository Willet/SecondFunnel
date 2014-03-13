/* To embed a SecondFunnel page into your site add the following inside the <BODY> tag of your <HTML> Page:
 * 
 * <div id="second-funnel-iframe-container"></div>
 * <script type="text/javascript" src="second_funnel_embed.js"></script>
 *
 * If you are not able to host the second_funnel_embed.js file. You can also copy and paste this file into
 * a <script> tag directly. Example:
 *
 * <div id="second-funnel-iframe-container"></div>
 * <script type="text/javascript">
 *      PASTE THE CODE IN HERE
 * </script>
 *
 * Normally the SecondFunnel script figures out the url automatically when the page is loaded based on what
 * domain and pathname the script is running on. For instance in the url "http://example.com/awesome/stuff";
 * the domain is 'example' and the pathname is '/awesome/stuff'. This script will see that, and load the
 * following in the iframe: 'http://example.secondfunnel.com/awesome/stuff'.
 *
 * If your domain has not been set up with SecondFunnel yet, you can specify a 'data-src' attribute in the
 * 'second-funnel-iframe-container' element. This attribute must point to a valid SecondFunnel page. This
 * way, you can test the SecondFunnel integration before the page for your specific domain has been set-up
 * by SecondFunnel. Example:
 *
 * <div id="second-funnel-iframe-container" data-src="http://test.secondfunnel.com/pref-tests/"></div>
 * <script type="text/javascript" src="second_funnel_embed.js"></script>
 *
 * This will load 'http://test.secondfunnel.com/pref-tests/' in the iframe regardless of the domain or
 * pathname it is running on.
 *
 * Note on IE 8 compatibility. The site hosting the script must specify a <!DOCTYPE html> at the top of the html file.
 */
(function () {
    try {
        //add events to the page in a cross browser way.
        var add_event_listener = function (element, event, callback) {
            if (element.addEventListener) {
              element.addEventListener(event, callback, false); 
            } else if (element.attachEvent)  {
              element.attachEvent('on' + event, callback);
            }
        };

        //remove events on a page in a cross browser way.
        var remove_event_listener = function (element, event, callback) {
            if (element.removeEventListener) {
                element.removeEventListener(event, callback, false);
            } else if (element.detachEvent) {
                element.detachEvent('on' + event, callback);
            }
        };
        
        //get the window height in a cross browser way.
        var get_inner_window_height = function () {
            if (window.innerHeight) {
                return window.innerHeight;
            }
            
            return document.documentElement.clientHeight;
        };
        
        //Get how far the page has scrolled in a cross browser way.
        var get_scroll_top = function () {
            return (window.pageYOffset !== undefined) ? window.pageYOffset : (document.documentElement || document.body.parentNode || document.body).scrollTop;
        };

        //get how high an element has been positioned on the page
        var get_absolute_top_offset = function (element) {
            var offset = 0;

            do {
                if (element.offsetTop) {
                    offset += element.offsetTop;
                }

                element = element.offsetParent;
            } while (element && element.offsetParent);

            return offset;
        };

        /*
         * Second funnel code
         */
        var second_funnel_container = document.getElementById('second-funnel-iframe-container'),
            second_funnel = document.createElement('iframe'),
            extend_iframe = function () {
                var new_height = document.documentElement.scrollHeight + 350;
                //increase the height of the iframe
                second_funnel.setAttribute('height', new_height);
                //send message to iframe to load more content
                second_funnel.contentWindow.postMessage(JSON.stringify({
                    'target': 'second_funnel',
                    'type': 'load_content',
                    'height': new_height
                }), origin);
            },
            url_parser = document.createElement('a'),
            url,
            origin,
            port,
            load_event_handler;

        //verify container element is correct
        if (!second_funnel_container) {
            console.error('No element with id: second-funnel-iframe-container was found');
        }

        url = second_funnel_container.getAttribute('data-src');

        //custom url not found, generating url automatically
        if (!url) {
            url = window.location.hostname.split('.');

            //we only care about the second to top level domain
            url = url[url.length - 2];

            url = 'http://' + url + '.secondfunnel.com' + window.location.pathname;
        }

        //parse origin from url
        url_parser.href = url;
        origin = url_parser.protocol + '//' + url_parser.host;
        port = origin.split(':');

        //port 80 is implied when the origin is passed in the message
        if (port.length > 2 && port[2] === '80') {
            origin = port[0] + ':' + port[1];
        }

        //creating the iframe
        second_funnel.setAttribute('id', 'second-funnel');
        second_funnel.setAttribute('src', url);
        second_funnel.setAttribute('seamless', 'seamless');
        second_funnel.setAttribute('width', '100%');
        second_funnel.setAttribute('height', get_inner_window_height());
        second_funnel.setAttribute('scrolling', 'no');
        second_funnel.setAttribute('style', 'overflow: hidden;');
        second_funnel_container.appendChild(second_funnel);

        //wait until load then attach the scroll listener
        load_event_handler = function () {
            add_event_listener(window, 'scroll', function () {
                var distanceToBottom = 75;
                if (get_scroll_top() + get_inner_window_height() > document.documentElement.scrollHeight - distanceToBottom) {
                    extend_iframe();
                }
            });

            add_event_listener(window, 'message', function (event) {
                var data;

                //Only accept messages from second funnel
                if (event.origin !== origin) {
                    return;
                }

                //Make sure data is in correct format
                try {
                    data = JSON.parse(event.data);
                } catch (error) {
                    return;
                }

                if (!data.type) {
                    return;
                }

                if (data.type === 'hash_change') {
                    if (data.hasOwnProperty('hash')) {
                        second_funnel.setAttribute('src', url + data.hash);

                        //Position information for the preview window
                        second_funnel.contentWindow.postMessage(JSON.stringify({
                            'target': 'second_funnel',
                            'type': 'window_location',
                            'window_middle': (get_scroll_top() + get_inner_window_height() / 2) - get_absolute_top_offset(second_funnel)
                        }), origin);
                    }
                }

            });

            remove_event_listener(second_funnel, 'load', load_event_handler);
        };

        add_event_listener(second_funnel, 'load', load_event_handler);
    } catch (error) {
        //if something goes wrong, do not affect the rest of the page.
    }
}());
