window.igniteCampaigns = window.igniteCampaigns || {};
window.igniteCampaigns.fn = window.igniteCampaigns.fn || {};

if( window.igniteCampaigns.fn.igniteGetScript === undefined ){
    window.igniteCampaigns.fn.igniteGetScript = function(n,t){var i=document.createElement("script"),r=document.getElementsByTagName("head")[0];i.src=n,done=!1,i.onload=i.onreadystatechange=function(){done||this.readyState&&this.readyState!="loaded"&&this.readyState!="complete"||(done=!0,i.onload=i.onreadystatechange=null,r.appendChild(i),t!==undefined&&t())},r.appendChild(i)}
}

var dependencies = [];
if( typeof jQuery === 'undefined' || jQuery.fn.on === undefined ){
    dependencies.push( 'http://ignitecampaigns.com/global/js/jquery-1.7.2.min.js' );
}
var prefix = (location.href.search( 'localhost' ) > -1 ? 'http://localhost/work/ignite/campaigns/ignite-campaigns' : 'http://ignitecampaigns.com' );
dependencies.push( 
    prefix + '/global/js/ignite.plugin.core.dev.js',
    prefix + '/global/js/ignite.range.js',
    prefix + '/global/js/ignite.ga.min.js'
);
window.igniteCampaigns.fn.igniteGetScript( prefix + '/utils/merge/?files=' + dependencies.join( ';' ), function(){
    (function($){
        //window.igniteCampaigns = window.igniteCampaigns || {};
        var x = new window.igniteCampaigns.PluginCore();
        var modules = {};
        modules.main = new window.igniteCampaigns.PluginCoreModule(
            'main',
            '',
            '<link href="http://fonts.googleapis.com/css?family=Open+Sans:800,600,400,700" rel="stylesheet" type="text/css">\
            <style>\
                #hypemcanvas-container{width:100%; background:#fff; color:#000; font-family: \'Open Sans\', sans-serif, arial black; color:#515151; position:relative; }\
                #hypemcanvas-container .watch{color:#fff !important; }\
                #hypemcanvas-container img{display:block; border:none; margin: auto; max-width: 480px; width: 100%; }\
                #hypemcanvas-container a, #hypemcanvas-container a:hover{text-decoration:none; color:#fff; }\
                aside.sidebar #hypemcanvas-container a, aside.sidebar #hypemcanvas-container a *{color:#fff; }\
                #hypemcanvas-container p{margin-top:5px; margin-bottom:5px; }\
                #hypemcanvas-container .hypemcanvas-container{position:relative; z-index:2; }\
                #hypemcanvas-container .hypemcanvas-containerpadding{padding:0px 12px; }\
                #hypemcanvas-container .hypemcanvas-header{overflow:hidden; }\
                #hypemcanvas-container .hypemcanvas-logo.otr-left{ }\
                #hypemcanvas-container .hypemcanvas-logo.otr-right{float:right; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer{list-style:none; max-height:448px; overflow-y:auto; padding:0px; margin:0px; }\
                #hypemcanvas-container ::-webkit-scrollbar{width:10px; }\
                #hypemcanvas-container ::-webkit-scrollbar-track{x-webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3); -webkit-border-radius: 10px; border-radius: 10px; }\
                #hypemcanvas-container ::-webkit-scrollbar-thumb{-webkit-border-radius: 10px; border-radius: 10px; background:#fff; -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.5); }\
                #hypemcanvas-container #hypemcanvas-rsscontainer li{float:left; display:block; border-bottom:1px solid #9e9e9e; width:100%; position:relative; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer li .controls{background:url(\'{{assetsurl}}img/hypem/controls.png\') no-repeat scroll 0px -120px transparent; width:20px; height:20px; width:20px; height:20px; position:absolute; right:5px; top:50%; margin-top:-10px; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer li.playing .controls{background-position:0px -140px; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer li.loading .controls{background:url(\'{{assetsurl}}img/hypem/loading.gif\') no-repeat scroll 0px 0px transparent; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer li.playing a{background-color:#f9f4e7; font-weight:bold; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer li.current a{background-color:#f9f4e7; font-weight:bold; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer li:last-child{border:none; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer a{font-size:12px; display:block; overflow:hidden; color:#515151; padding:9px 0px 9px 9px; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer a:hover{background-color:#f9f4e7; font-weight:bold; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer a .artist{color:#102b56; display:block; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer a .title{display:block; color:#515151; }\
                xaside.sidebar #hypemcanvas-container #hypemcanvas-rsscontainer a:hover, xaside.sidebar #hypemcanvas-container #hypemcanvas-rsscontainer a:hover *{color:#fff;}\
                #hypemcanvas-container #hypemcanvas-rsscontainer a img{border:1px solid #c2c2c2; float:left; margin-right:7px; width:43px; box-sizing:border-box; -moz-box-sizing:border-box; }\
                #hypemcanvas-container #hypemcanvas-rsscontainer a p{float:left; margin:0px; max-width:199px; }\
                .ie #hypemcanvas-container #hypemcanvas-rsscontainer a p{max-width:200px; }\
                #hypemcanvas-container .large-font{font-size:20px; }\
                #hypemcanvas-container .notlarge-font{font-size:14px; }\
                #hypemcanvas-container .hypemcanvas-clickthru{position:absolute; top:0px; left:0px; display:block; width:100%; height:100%; background:transparent; }\
                aside.sidebar #hypemcanvas-container a.seeall, #hypemcanvas-container .seeall{background:#fff; width:87px; height:19px; text-align:center; margin:0px auto; color:#000; display:block; font-size:11px; line-height:19px; font-weight:700; position:absolute; left:50%; margin-left:-44px; bottom:2px; }\
                #hypemcanvas-container .seeall:hover{color:#000; }\
                #ignite-aside .ignite-aside-copy-container{margin-top:10px; }\
                #hypemcanvas-container .off{opacity:0; filter:alpha(opacity=0); }\
                #hypemcanvas-container .hypemcanvas-loadinganim img{margin:0px auto; }\
                #hypemcanvas-container .hypemcanvas-controlpanel{height:40px; padding:0px 0px; background:#000; overflow:hidden; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .control{float:left; padding:10px 0px; border-left:1px solid #404040; cursor:pointer; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .control div{width:30px; height:20px; background:url(\'{{assetsurl}}img/hypem/controls.png\') no-repeat scroll center 0px transparent; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-prev div{background-position:center -80px; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-next{border-right:1px solid #404040; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-next div{background-position:center -60px; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-playpause.playing div{background-position:center -20px; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-volume{float:right; border-left:1px solid #404040; border-right:none; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-popup{float:right; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-volume div{background-position:center -160px; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-volume.mute div{background-position:center -100px; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .controlpanel-popup{border:none; text-align:center; padding:0px 13px; }\
                #hypemcanvas-container .hypemcanvas-controlpanel .off{display:none; }\
                #hypemcanvas-container .ignite-range{width:300px; height:10px; background:#fff; position:relative; }\
                #hypemcanvas-container .ignite-range .ignite-rangethumb{width:5%; height:100%; background:#333; cursor:pointer; position:absolute; top:0px; left:0px; box-sizing:border-box; -moz-box-sizing:border-box; box-shadow:0px 0px 6px 0px #333; z-index:1; }\
                #hypemcanvas-container .ignite-range .ignite-rangemask{position:absolute; left:0px; top:0px; width:100%; height:100%; cursor:pointer; z-index:2; }\
                #hypemcanvas-container .ignite-range .ignite-rangebar{position:absolute; height:2px; width:310px; background:#333; border-radius:1px; top:4px; left:-5px;  }\
                #hypemcanvas-container .ignite-range.vertical{height:300px; width:20px; background:#fff; position:relative; }\
                #hypemcanvas-container .ignite-range.vertical .ignite-rangethumb{height:5%; width:100%; background:#333; cursor:pointer; position:absolute; top:0px; left:0px; box-sizing:border-box; -moz-box-sizing:border-box; box-shadow:0px 0px 6px 0px #333; z-index:1; }\
                #hypemcanvas-container .ignite-range.vertical .ignite-rangemask{position:absolute; left:0px; top:0px; width:100%; height:100%; cursor:pointer; z-index:2; }\
                #hypemcanvas-container .ignite-range.vertical .ignite-rangebar{position:absolute; width:2px; height:310px; background:#333; border-radius:1px; left:4px; top:0px;  }\
                #hypemcanvas-container #controlpanel-volume-control{height:50px; position:absolute; top:359px; left:444px; background:transparent; opacity:1; }\
                #hypemcanvas-container #controlpanel-volume-control .ignite-rangebar{width:0px; height:0px; border-style:solid; border-width:0px 18px 54px 0px; border-color:transparent #000000 transparent transparent; border-radius:0px; left:0px; background:transparent; }\
                #hypemcanvas-container #controlpanel-volume-control .ignite-rangethumb{background:#fff; background:rgba(255,255,255,0.7); width:120%; left:-2px; border:1px solid #000; }\
                #hypemcanvas-container #controlpanel-volume-control.hide{opacity:0; width:0px; }\
                .ignite-loader{text-align: center; background:none; }\
                .ignite-loader.css3 span{display:inline-block; vertical-align:middle; width:10px; height:10px; margin:50px auto; background:#000; border-radius:50px; -webkit-animation:loader 0.9s infinite alternate; -moz-animation: loader 0.9s infinite alternate; }\
                .ignite-loader.css3.big{position:absolute; top:40%; left:45%; xtransform:scale(2); x-webkit-transform:scale(2); }\
                .ignite-loader.css3 span:nth-of-type(2) {-webkit-animation-delay: 0.3s; -moz-animation-delay: 0.3s;}\
                .ignite-loader.css3 span:nth-of-type(3) {-webkit-animation-delay: 0.6s; -moz-animation-delay: 0.6s;}\
                @-webkit-keyframes loader {\
                  0% {\
                    width: 5px;\
                    height: 5px;\
                    opacity: 0.9;\
                    -webkit-transform: translateY(0);\
                  }\
                  100% {\
                    width: 10px;\
                    height: 10px;\
                    opacity: 0.1;\
                    -webkit-transform: translateY(-21px);\
                  }\
                }\
                @-moz-keyframes loader {\
                  0% {\
                    width: 10px;\
                    height: 10px;\
                    opacity: 0.9;\
                    -moz-transform: translateY(0);\
                  }\
                  100% {\
                    width: 24px;\
                    height: 24px;\
                    opacity: 0.1;\
                    -moz-transform: translateY(-21px);\
                  }\
                }\
                .animate{-webkit-transition:all 0.4s cubic-bezier(0.2, 0.6, 0.3, 1) 0s; -moz-transition:all 0.4s cubic-bezier(0.2, 0.6, 0.3, 1) 0s; -o-transition:all 0.4s cubic-bezier(0.2, 0.6, 0.3, 1) 0s; transition:all 0.4s cubic-bezier(0.2, 0.6, 0.3, 1) 0s; }\
            </style>\
            <div id="hypemcanvas-container">\
                <a href="{{clickthru}}" target="_blank" class="hypemcanvas-clickthru gatrack"></a>\
                <div class="hypemcanvas-header hypemcanvas-container">\
                    <a href="{{clickthru}}" target="_blank" class="hypemcanvas-logo otr-left gatrack">\
                        <img src="{{banner}}" />\
                    </a>\
                </div>\
                <div class="hypemcanvas-controlpanel hypemcanvas-container"><div class="controlpanel-prev control"><div></div></div><div class="controlpanel-playpause control"><div></div></div><div class="controlpanel-next control"><div></div></div><div class="controlpanel-volume control"><div></div></div><div class="controlpanel-popup control {{showpopup}}"><img src="{{assetsurl}}img/hypem/popup.jpg"/></div></div>\
                <div class="ignite-range hide hypemcanvas-container" data-value="0" id="controlpanel-volume-control"><div class="ignite-rangethumb"></div><div class="ignite-rangebar"></div><a title="Slide to Change Volume" class="ignite-rangemask" href="javascript:void(0);"></a></div>\
                <ul id="hypemcanvas-rsscontainer" class="hypemcanvas-container hypemcanvas-containerpadding off animate"></ul>\
                <a class="hypemcanvas-footer gatrack hypemcanvas-container" href="{{clickthru2}}" target="_blank"><img src="{{footerImage}}"/></a>\
                <div class="hypemcanvas-loadinganim hypemcanvas-container">{{loadinganim}}</div>\
            </div>',
            {},
            function( m, o, callback ){
                var w = window.top, d=w.document,
                container = $( '#hypem-playlist-container' ).parent();
                container.append( m.markup );
                if( o.vars.isIE ){
                    container.addClass( 'ie' );
                }
                //o.fn.firePixels( o.vars.pixels );
            }
        ).setFn( 'initTemplates', function( module, o ){
            var overrides = window.igniteCampaigns.hypemplaylist.overrides;
            o.fn.addTemplate( module.id, 'showpopup', overrides.hidepopup===1?'off':'' );
            o.fn.addTemplate( module.id, 'clickthru2', overrides.clickthru2?overrides.clickthru2:'javascript:' );
            o.fn.addTemplate( module.id, 'banner', overrides.banner?overrides.banner:'http://wac.450f.edgecastcdn.net/80450F/ignitecampaigns.com/national/playlist/assets/img/hypem/logo.jpg?v=3' );
            o.fn.addTemplate( module.id, 'footerImage', overrides.footerImage?overrides.footerImage:'http://ignitecampaigns.com/national/playlist/assets/img/hypem/footer.jpg' );
        });
        
        modules.GA = new window.igniteCampaigns.PluginCoreModule(
            'GA',
            '',
            '',
            {},
            function( m, o, callback ){
                var ga = new window.igniteCampaigns.GAHelper();
                ga.setAccounts({
                    campaignId:'UA-19109753-46'
                }).
                setCat( 'Playlist - HM' ).
                init();
                o.vars.gahelper = ga;
                $( '#hypemcanvas-container' ).on( 'click', '.gatrack', function(e){
                    //e.preventDefault();
                    var elem = this,
                    $elem = $( elem );
                    /*window.setTimeout(function(){
                        window.top.location.href = elem.href;
                    });*/
                    if( $elem.hasClass( 'hypemcanvas-logo' ) ){
                        ga.gaTrackEvent( 'clickthrough: sponsor', elem.href );
                    }else if( $elem.hasClass( 'hypemcanvas-footer' ) ){
                        ga.gaTrackEvent( 'clickthrough: HM', elem.href );
                    }
                });
                ga.gaTrackEvent( 'impression', window.top.location.href );
                o.vars.channel.on( 'ignite-track-event', function(e,o){
                    ga.gaTrackEvent( o.action, o.label );
                });
            }
        );
        modules.audio = new window.igniteCampaigns.PluginCoreModule(
            'audio',
            '',
            '',
            {
                //url:'http://api.hypem.com/playlist/special/gap_gvb/json/1/data.js?key=48ea0ae3de02f8046ffbf2e70ffd78bf'
            },
            function( m, o, callback ){
                var vars = m.vars,
                    container = $( '#hypemcanvas-container' ),
                    player = new Audio(),
                    //url = o.vars.urls.utilsurl + vars.url,
                    url = vars.url,
                    playlist = [],
                    PlaylistItem = function( obj ){
                        var self = this,
                            template = '<li tabindex="{{id}}"><a class="playlist-item-{{id}} gatrack" href="javascript:" rel="no-follow"><img src="{{image}}" /><p><span class="artist">{{artist}}</span><span class="title">{{title}}</span></p><span class="controls"></span></a></li>',
                            map = [ 'id', 'image', 'artist', 'title' ],
                            getMediaUrl = function( url, callback ){
                                if( PlaylistItem.mediaAjax !== undefined ){
                                    audioContainer.find( 'li' ).removeClass( 'loading' );
                                    PlaylistItem.mediaAjax.abort();
                                }
                                PlaylistItem.mediaAjax = $.ajax({
                                    url:o.vars.urls.baseurl + 'national/playlist/hypeminterface.php?callback=?',
                                    dataType:'jsonp',
                                    data:{
                                        url:url
                                    },
                                    beforeSend:function(){
                                        self.obj.addClass( 'loading' );
                                    },
                                    success:function( data ){
                                        self.obj.removeClass( 'loading' );
                                        if( data.status === 'success' ){
                                            callback( data.data.url, data.data.content_type );
                                        }
                                    }
                                });
                            };
                        
                        self.media = {
                                mp3:'http://hypem.com/serve/public/' + obj.mediaid
                        };
                        self.image = obj.image
                        self.id = obj.id;
                        self.title = obj.title;
                        self.artist = obj.artist;
                        
                        self.centerObj = function(){
                            self.obj.focus();
                        };
                        
                        self.clickHandler = function( triggerevent ){
                            audioContainer.find( 'li' ).removeClass( 'loading' );
                            if( !self.obj.hasClass( 'playing' ) ){
                                var callback = function(){
                                    audioContainer.find( 'li' ).removeClass( 'playing' );
                                    self.play();
                                    self.obj.addClass( 'playing' );
                                    self.centerObj();
                                };
                                if( !self.playurl ){
                                    getMediaUrl( self.media.mp3, function( mediaurl, mime ){
                                        if( player.canPlayType( mime ) ){
                                            self.playurl = mediaurl;
                                            callback();
                                        }else{
                                            try{
                                            console.log( 'Cant play media type: ' + mime );
                                            }catch(e){}
                                            var i = self.id === playlist.length - 1 ? 0 : self.id + 1;
                                            playlist[ i ].clickHandler( triggerevent );
                                        }
                                    });
                                }else{
                                    callback();
                                }
                                if( triggerevent !== undefined ){
                                    o.vars.channel.trigger( 'ignite-track-event', { action:triggerevent, label:self.title });
                                }
                            }else{
                                self.pause();
                                self.obj.removeClass( 'playing' );
                                o.vars.channel.trigger( 'ignite-track-event', { action:'user click: pause', label:self.title });
                            }
                        };
                        self.play = function(){
                            if( player.src !== self.playurl ){
                                player.src = self.playurl;
                            }
                            player.play();
                            if( !self.obj.hasClass( 'current' ) ){
                                PlaylistItem.current = self.id;
                                audioContainer.find( 'li' ).removeClass( 'current' );
                                self.obj.addClass( 'current' );
                            }
                        };
                        self.pause = function(){
                            player.pause();
                            if( self.obj.hasClass( 'playing' ) ){
                                self.obj.removeClass( 'playing' );
                            }
                        };
                        self.init = function(){
                            var html = self.getMarkup();
                            self.obj = $( html );
                            self.obj.on( 'click', function(){self.clickHandler( 'user click: song' )});
                            return self;
                        };
                        self.getObj = function(){
                            return self.obj;
                        };
                        self.getMarkup = function(){
                            var html = template;
                            for( var i=0;i<map.length;i++ ){
                                var reg = new RegExp( '{{' + map[ i ] + '}}', "g" );
                                html = html.replace( reg, self[ map[ i ] ] );
                            }
                            self.html = html;
                            return html;
                        };
                        return self;
                    },
                    audioContainer = container.find( '#hypemcanvas-rsscontainer' ),
                    controlPanel = container.find( '.hypemcanvas-controlpanel' ),
                    popupmarkup = 
                        '<!DOCTYPE html>\
                            <html>\
                            <head>\
                                <meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">\
                                <title>Hype Machine\'s Playable Schedule</title>\
                                <style>body{padding:0px; margin:0px; width:470px; height:942px; }html{width:470px; height:942px; overflow:hidden; }</style>\
                            </head>\
                            <body>\
                                <script type="text/javascript">var w = window;\
                                    w.igniteCampaigns = w.igniteCampaigns || {};\
                                    w.igniteCampaigns.hypemplaylist = w.igniteCampaigns.hypemplaylist || {};\
                                    w.igniteCampaigns.hypemplaylist.overrides = {\
                                        clickthru:\'{{clickthru}}\',\
                                        clickthru2:\'{{clickthru2}}\',\
                                        hidepopup:1,\
                                        initid:{{initid}},\
                                        banner:\'{{banner}}\',\
                                        footerImage:\'{{footerImage}}\',\
                                        playlisturl:\'{{playlisturl}}\'\
                                    };\
                                </script>\
                                <script type="text/javascript" id="ignite-hypem-audioplayer" src="{{baseurl}}national/playlist/js/launchhypemembed.js?'+new Date().getTime()+'"></script>\
                                <div id="hypem-playlist-container"></div>\
                            </body>\
                        </html>',
                    initControlPanel = function(){
                        var play = controlPanel.find( '.controlpanel-playpause' ),
                            prev = controlPanel.find( '.controlpanel-prev' ),
                            next = controlPanel.find( '.controlpanel-next' ),
                            volume = controlPanel.find( '.controlpanel-volume' ),
                            volumeControl = container.find( '#controlpanel-volume-control' ),
                            v = new window.igniteCampaigns.Range({
                                id:'controlpanel-volume-control',
                                start:10,
                                step:11,
                                isVertical:1
                            }),
                            $player = $( player );
                        
                        player.onplay = function(){
                            play.addClass( 'playing' );
                        };
                        player.onpause = function(){
                            play.removeClass( 'playing' );
                        };
                        player.onended = function(){
                            o.vars.channel.trigger( 'ignite-track-event', { action:'song: complete', label:playlist[ PlaylistItem.current ].title });
                            play.removeClass( 'playing' );
                            if( PlaylistItem.current!==undefined ){
                                var i = PlaylistItem.current === playlist.length - 1 ? 0 : PlaylistItem.current + 1;
                                playlist[ i ].clickHandler( 'autoplay: playlist next' );
                            }
                        };
                        player.onerror = function(){
                        };
                        window.player = player;
                        controlPanel.on( 'click', '.control', function(){
                            var elem = this,
                            $elem = $( this );
                            if( $elem.hasClass( 'controlpanel-prev' ) ){
                                if( PlaylistItem.current!==undefined ){
                                    var i = PlaylistItem.current === 0 ? playlist.length - 1 : PlaylistItem.current - 1;
                                    playlist[ i ].clickHandler( 'user click: prev' );
                                }
                            }else if( $elem.hasClass( 'controlpanel-next' ) ){
                                if( PlaylistItem.current!==undefined ){
                                    var i = PlaylistItem.current === playlist.length - 1 ? 0 : PlaylistItem.current + 1;
                                    playlist[ i ].clickHandler( 'user click: next' );
                                }
                            }else if( $elem.hasClass( 'controlpanel-playpause' ) ){
                                if( !PlaylistItem.current ){
                                    playlist[ 0 ].clickHandler( 'user click: play' );
                                }else{
                                    playlist[ PlaylistItem.current ].clickHandler( 'user click: play' );
                                }
                            }else if( $elem.hasClass( 'controlpanel-volume' ) ){
                                if( volumeControl.hasClass( 'hide' ) ){
                                    o.vars.channel.trigger( 'ignite-track-event', { action:'user click: volume', label:'' });
                                    volumeControl.removeClass( 'hide' );
                                }else{
                                    volumeControl.addClass( 'hide' );
                                }
                            }else if( $elem.hasClass( 'controlpanel-popup' ) ){
                                var playerpopup = window.open( '', 'hypemplayer'+new Date().getTime(), 'width=470,height=942,resizeable=0,scrollbars=0,location=0,toolbar=0' ),
                                    d = playerpopup.document,
                                    overrides = window.igniteCampaigns.hypemplaylist.overrides;
                                d.write(
                                    popupmarkup.replace( /{{baseurl}}/g, o.vars.urls.baseurl )
                                        .replace( /{{clickthru}}/g, overrides.clickthru || 'javascript:void(0);' )
                                        .replace( /{{clickthru2}}/g, overrides.clickthru2 || 'javascript:void(0);' )
                                        .replace( /{{initid}}/g, PlaylistItem.current )
                                        .replace( /{{banner}}/g, overrides.banner )
                                        .replace( /{{footerImage}}/g, overrides.footerImage )
                                        .replace( /{{playlisturl}}/g, overrides.playlisturl )
                                );
                                d.close();
                                o.vars.channel.trigger( 'ignite-track-event', { action:'user click: popup', label:'' });
                                playlist[ PlaylistItem.current ].pause();
                            }
                        });
                        volumeControl.on( 'ignite-range-valuechange', function( e, o ){
                            player.volume = o.newval / 10;
                            
                            if( o.newval === 0 ){
                                volume.addClass( 'mute' );
                            }else{
                                volume.removeClass( 'mute' );
                            }
                        });
                    };
                //$.support.cors = true;
                $.ajax({
                    url:url+"&callback=?",
                    dataType:'jsonp',
                    beforeSend:function(){
                        $( '#hypemcanvas-container .hypemcanvas-loadinganim' ).append( o.vars.loadingAnim );
                    },
                    success:function( d ){
                        var html = '';
                        $( '#hypemcanvas-container .hypemcanvas-loadinganim' ).remove();
                        //console.log( d );
                        if( d ){
                            for( var i in d ){
                                if( i >= 50 ){
                                    break;
                                }
                                if( d[i] !== undefined && typeof d[i] === 'object' ){
                                    if( d[i].pub_audio_unavail && d[i].pub_audio_unavail === true ){}else{
                                        var playlistItem = new PlaylistItem({
                                            mediaid:d[i].mediaid,
                                            id:parseInt( i, 10 ),
                                            title:d[i].title,
                                            artist:d[i].artist,
                                            image:d[i].thumb_url
                                        }).init();
                                        playlist.push( playlistItem );
                                        audioContainer.append( playlistItem.getObj() );
                                    }
                                    //html += playlistItem.getMarkup();
                                }
                            }
                            //audioContainer.append( html ).removeClass( 'off' );
                            audioContainer.removeClass( 'off' );
                            initControlPanel();
                            if( window.igniteCampaigns.hypemplaylist.overrides.initid !== undefined ){
                                playlist[ window.igniteCampaigns.hypemplaylist.overrides.initid ].clickHandler();
                            }
                        }
                    }
                });
            }
        ).setVar( 'url', window.igniteCampaigns.hypemplaylist.overrides.playlisturl || 'http://api.hypem.com/playlist/special/gap_gvb/json/1/data.js?key=48ea0ae3de02f8046ffbf2e70ffd78bf' );
        x.  
            setVar( 'clickthru', window.igniteCampaigns.hypemplaylist.overrides.clickthru || 'javascript:void(0);' ).
            setVar( 'pixels', window.igniteCampaigns.hypemplaylist.overrides.pixels || [] ).
            /*setVar( 'gacategory', {
                canvas:'Supervideo',
                aside:'Vertical Hub'
            }).
            setVar( 'GA', {
                test:{
                    igniteId:'UA-39848203-1',
                    campaignId:'UA-39848203-3'
                },
                live:{
                    igniteId:'UA-39968433-1',
                    campaignId:'UA-39968433-20'
                }
            }).*/
            setVar( 'urls', {
                live:{
                    baseurl:'http://ignitecampaigns.com/',
                    utilsurl:'http://ignitecampaigns.com/utils/',
                    assetsurl:'http://wac.450f.edgecastcdn.net/80450F/ignitecampaigns.com/national/playlist/assets/'
                },
                test:{
                    baseurl:'http://localhost/work/ignite/campaigns/ignite-campaigns/',
                    utilsurl:'http://localhost/work/ignite/campaigns/ignite-campaigns/utils/',
                    assetsurl:'http://localhost/work/ignite/campaigns/ignite-campaigns/national/playlist/assets/'
                }
            }).
            addModule( 'main', modules.main ).
            addModule( 'rss', modules.audio ).
            addModule( 'GA', modules.GA ).
            init();
    })(jQuery);
});
