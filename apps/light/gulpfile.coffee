gulp = require("gulp")
path = require("path")
merge = require('merge-stream')
$ = require("gulp-load-plugins")() # load all gulp plugins
shell = require("gulp-shell")
mainBowerFiles = require("main-bower-files")
browserify = require("browserify")
browserifyShim = require("browserify-shim")
source = require("vinyl-source-stream2")
through = require("through2")
BrowserSync = require("browser-sync")
browserifyConfig = require("./package.json")
watchify = require('watchify')
_ = require('underscore')
runSequence = require('run-sequence')

# versioning stuff, it is harder than one would think
rev = require('gulp-rev')
revOutdated = require('gulp-rev-outdated')
revCollector = require('gulp-rev-collector')

# location of file sources
# (try to keep the file-lists in alphabetical order)
sources =
    base: "src"
    scripts: [
        "src/ad/**/*.js"
        "src/clients/**/*.js"
        "src/demo/**/*.js"
        "src/landingpage/**/*.js"
    ]
    fonts: [
        "src/demo/**/*.{eot,svg,ttf,woff}"
        "src/clients/**/*.{eot,svg,ttf,woff}"
        "src/components/**/*.{eot,svg,ttf,woff}"
    ]
    sass: [
        "src/clients/**/*.scss"
        "src/demo/**/*.scss"
    ]
    images: [
        "src/clients/**/*.{gif,png,jpg,jpeg,svg}"
        "src/components/**/*.{gif,png,jpg,jpeg,svg}"
        "src/demo/**/*.{gif,png,jpg,jpeg,svg}"
        "src/shared/**/*.{gif,png,jpg,jpeg,svg}"
    ]
    pages_no_modify: [
        "src/demo/**/index.html"
    ]
    pages: [
        "src/clients/**/landingpage/*/index.html"
        "src/clients/**/ad/*/index.html"
    ]
    browserify: [
        "src/clients/**/main.js"
    ]
    vendor: [ # all these are taken as is
        "src/clients/**/media_player/{launchhypemcanvas3.js,player.html}"
    ]


static_output_dir = "static/light"
static_serve_dir = "static/light"
template_output_dir = "templates/light"
bower_dir = "lib/"
config = production: true

onError = (err) ->
    $.util.log($.util.colors.red("\n\nPlumber: Error: #{err}\n\n"))
    $.util.beep()
    console.error err
    return

gulp.task "build", [
    "bower"
    "html"
    "styles"
    "scripts"
    "images"
    "fonts"
    "vendor"
]

gulp.task "default", ["clean"], ->
    gulp.start "build"


gulp.task "clean", ->
    gulp.src([static_output_dir, template_output_dir], read: false)
        .pipe $.if(config.production, revOutdated(2)) # keep 2 most recent assets in production
        .pipe $.size(showFiles: true, title: $.util.colors.cyan("clean"))
        .pipe $.rimraf()

gulp.task "destroy", ->
    gulp.src([static_output_dir, template_output_dir], read: false)
        .pipe $.rimraf()


gulp.task "bower", ->
    $.bower().pipe gulp.dest(bower_dir)

gulp.task "vendor", ->
    gulp.src(sources.vendor)
        .pipe gulp.dest(static_output_dir)

gulp.task "html", ["rev"], ->
    pages_no_modify = gulp.src(sources.pages_no_modify)
    pages = gulp.src sources.pages
        .pipe $.plumber(errorHandler: onError)
        .pipe $.include() # run through file includes
        .pipe $.fileInclude(basepath: __dirname + "/" + sources.base)

    manifest = gulp.src("#{static_output_dir}/rev-manifest.json")

    return merge(manifest, pages, pages_no_modify)
        .pipe $.plumber(errorHandler: onError)
        .pipe $.if(config.production, revCollector())
        .pipe $.filter("**/*.html") # ignore the manifest
        .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("all-rev-modified-files"))
        .pipe gulp.dest(template_output_dir)
        .pipe BrowserSync.reload(stream: true, once: true)
        .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("html"))


gulp.task "styles", ->
    gulp.src(sources.sass)
        .pipe $.plumber(errorHandler: onError)
        .pipe $.sass(
            errLogToConsole: not config.production
            style: (if config.production then "compressed" else "nested")
            sourcemap: true
        )
        .pipe $.autoprefixer("last 3 version", "safari 6", "ie 8", "ie 9", "opera 12.1", "ios 6", "android 4")
        .pipe gulp.dest(static_output_dir) # output normal
        .pipe BrowserSync.reload(stream: true)
        .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("styles"))


gulp.task "scripts", ["bower"], ->
    bundlerTransform = (file, encoding, callback) ->
        self = this
        filename = path.resolve(file.path)
        filenameRelative = path.relative(file.base, file.path)

        bundler = browserify(
            cache: {}
            packageCache: {}
            fullPaths: true
            basedir: __dirname
            commondir: false
            insertGlobals: false
            debug: true # we always want those source maps
            entries: filename
            extensions: [".coffee"] # extensions you do not need to put on a require
        )
        rebundle = (bundler) ->
            bundler.plugin(
                'minifyify',
                # where the map file is served from
                map: "/#{static_serve_dir}/#{filenameRelative}.map"
                # where the map file is saved to
                output: "#{static_output_dir}/#{filenameRelative}.map"
                minify: config.production
                # conversions to make map paths relative (currently breaks browserify-shim)
                #compressPath: (filepath) ->
                #    return path.relative(__dirname, filepath)
            )
            return bundler.bundle()
                .on('error', $.util.log.bind($.util, 'Browserify Error'))
                .pipe source(file)
                .pipe gulp.dest(static_output_dir) # output normal
                .pipe BrowserSync.reload(stream: true, once: true)
                .on 'end', callback
                .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("scripts"))

        if not config.production
            # use watchify for faster builds in development
            bundler = watchify bundler
            bundler.on 'update', ->
                $.util.log($.util.colors.cyan("scripts: (rebuilding)"), filenameRelative)
                rebundle bundler

        return rebundle(bundler)

    return gulp.src(sources.browserify)
        .pipe through.obj(bundlerTransform) # NOTE: cannot pipe anything else


gulp.task "images", ->
    return gulp.src(sources.images)
        .pipe $.plumber(errorHandler: onError)
        .pipe $.newer(static_output_dir)
        .pipe $.imagemin(
            optimizationLevel: 3
            progressive: true
            interlaced: true
        )
        .pipe gulp.dest(static_output_dir)
        .pipe BrowserSync.reload(stream: true, once: true)
        .pipe $.size()


gulp.task "fonts", ["bower"], ->
    return gulp.src(sources.fonts)
        .pipe gulp.dest(static_output_dir)

gulp.task "rev", (cb) ->
    if config.production # we need to actually revision the files
        runSequence "_rev", cb
    else
        cb()
    return

gulp.task "_rev", ["images", "fonts", "scripts", "styles"], ->
    # grab all the assets that don't need modified but should be reved
    reved_suffix = ".revv"
    return gulp.src(
        [
            "#{static_output_dir}/**/*.{css,js,jpeg,jpg,svg,gif,png,eot,woff,ttf}",
            # exclude already reved files (previous versions, etc)
            "!#{static_output_dir}/**/*#{reved_suffix}.{css,js,jpeg,jpg,svg,gif,png,eot,woff,ttf}"
        ], { base: __dirname })
        .pipe $.plumber(errorHandler: onError)
        .pipe rev()
        .pipe $.rename(suffix: reved_suffix)
        .pipe gulp.dest(__dirname) # output rev-files
        .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("rev"))
        .pipe rev.manifest() # replace pipeline with rev-manifest
        .pipe gulp.dest(static_output_dir) # output manifest
        .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("rev-manifest"))


#
# Programmer Helpers
#

gulp.task "lint", ["jslint", "coffeelint"]


gulp.task "jslint", ->
    js_lint = gulp.src(sources.scripts)
        .pipe($.jshint())
        .pipe $.jshint.reporter(require("jshint-stylish"))

gulp.task "coffeelint", ->
    gulp.src(["src/**/*.coffee", "gulpfile.coffee"])
        .pipe($.coffeelint())
        .pipe $.coffeelint.reporter()

#
# Development Environment
#
gulp.task "set-development", ->
    config.production = false
    return

collectstatic = ->
    grey = "tput setaf 8"
    black = "tput sgr0"
    bell = "tupt bel"
    time = "date +\"%T\""
    $.util.log(("Starting collect static files"))
    # for gulp-shell to work, it needs to be in a pipe or task
    gulp.src('', {read: false})
        .pipe( shell(["sudo python manage.py collectstatic --noinput",
                      "echo \"\[$(#{grey})$(#{time})$(#{black})\] Finished collecting static files $(tput bel)$(tput bel)$(tput bel)\""],
                     {cwd: '/opt/secondfunnel/app'}) )

tCollectstatic = _.throttle(collectstatic, 5000)

gulp.task "dev", [
    "set-development"
    #"build"
], ->
    collectstatic()

    BrowserSync
        proxy:
            host: "2ndfunnel.com/" + static_output_dir
            port: 8000

        watchOptions:
            debounce: 500 # wait 0.5 seconds incase more changes come

        notify: true # whether to notify the browser when changes were made

    gulp.watch "src/**/*.html", -> 
        gulp.start ["html"], tCollectstatic
    gulp.watch sources.sass, ->
        gulp.start ["styles"], tCollectstatic
    gulp.watch sources.fonts, ->
        gulp.start ["fonts"], tCollectstatic
    gulp.watch sources.images, ->
        gulp.start ["images"], tCollectstatic
    gulp.watch sources.vendor, ->
        gulp.start ["vendor"], tCollections
    $.util.log($.util.colors.blue("watch'ing html, styles, fonts, images, vendor"))
    return

