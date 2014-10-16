gulp = require("gulp")
path = require("path")
merge = require('merge-stream')
$ = require("gulp-load-plugins")() # load all gulp plugins
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
exorcist = require('exorcist')
transform = require('vinyl-transform')


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

# see https://github.com/mishoo/UglifyJS2#compressor-options for additional options
uglify_options =
    mange: true
    preserveComments: "some" # only copyright etc (closure compilation directives etc)

onError = (err) ->
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
        .pipe $.if(config.production, revCollector())
        .pipe $.filter("**/*.html") # ignore the manifest
        .pipe gulp.dest(template_output_dir)
        .pipe BrowserSync.reload(stream: true, once: true)
        .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("html"))


gulp.task "styles", ->
    gulp.src(sources.sass)
        .pipe $.sass(
            errLogToConsole: not config.production
            style: (if config.production then "compressed" else "nested")
            sourcemap: true
        )
        .pipe $.autoprefixer("last 3 version", "safari 6", "ie 8", "ie 9", "opera 12.1", "ios 6", "android 4")
        .pipe gulp.dest(static_output_dir) # output normal
        .pipe BrowserSync.reload(stream: true)
        .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("styles"))


gulp.task "scripts", ["bower"], () ->
    #
    # Heavily inspired by https://github.com/greypants/gulp-starter/blob/master/gulp/tasks/browserify.js
    #

    browserifyTransform = (file, encoding, cb) ->
        filenameRelative = path.relative(file.base, file.path)
        bundleConfig =
            entries: file
            dest: static_output_dir
            outputName:
                base: file.base
                path: file.path

        bundler = browserify(
            # watchify args
            cache: {}
            packageCache: {}
            fullPaths: true
            # relative dir to use for root
            basedir: __dirname
            # the entry point of the application
            entries: bundleConfig.entries
            # add file extensions that are optional for require statements
            extensions: [".coffee"]
            # enable source maps
            debug: true
        )

        bundler.plugin(
           'minifyify',
           minify: if config.production then uglify_options else false
           # where the map file is served from
           map: "/#{static_serve_dir}/#{filenameRelative}.map"
           # where the map file is saved to
           output: "#{static_output_dir}/#{filenameRelative}.map"
        )

        bundle = ->
            $.util.log("'#{$.util.colors.cyan("scripts")}'", "Bundling", $.util.colors.blue(filenameRelative), "...")
            bundler.bundle()
                # report compilation errors
                .on 'error', $.util.log.bind($.util, 'Browserify Error')
                .pipe exorcist(
                    # sourcemap output location
                    file: "#{static_output_dir}/#{filenameRelative}.map"
                    # sourcemap url location
                    url: "/#{static_serve_dir}/#{filenameRelative}.map"
                )
                # vinyl-source-stream to make stream gulp-compatible
                .pipe source(bundleConfig.outputName)
                # output destination
                .pipe gulp.dest(static_output_dir)
                # notify of end of stream etc
                .pipe through.obj(endCallback)

        endCallback = (bundle) =>
            $.util.log("'#{$.util.colors.cyan("scripts")}'", "Bundled", $.util.colors.blue(filenameRelative))
            # add the bundle to the output stream of the transform
            @push bundle
            # notify finished
            cb()

        unless config.production
            # Wrap with watchify and rebundle on changes
            bundler = watchify(bundler)
            # Rebundle on update
            bundler.on 'update', bundle

        return bundle()

    return gulp.src sources.browserify
        .pipe through.obj(browserifyTransform)
        #.pipe BrowserSync.reload(stream: true)
        .pipe $.size(showFiles: true, gzip: true, title: $.util.colors.cyan("scripts"))


gulp.task "images", ->
    return gulp.src(sources.images)
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
    js_lint = gulp.src(sources.scripts).pipe($.jshint()).pipe $.jshint.reporter(require("jshint-stylish"))

gulp.task "coffeelint", ->
    gulp.src(["src/**/*.coffee", "gulpfile.coffee"]).pipe($.coffeelint()).pipe $.coffeelint.reporter()

#
# Development Environment
#
gulp.task "set-development", ->
    config.production = false
    return

gulp.task "dev", [
    "set-development"
    "build"
], ->
    BrowserSync
        proxy:
            host: "2ndfunnel.com/" + static_output_dir
            port: 8000

        watchOptions:
            debounce: 500 # wait 0.5 seconds incase more changes come

        notify: true # whether to notify the browser when changes were made

    gulp.watch "src/**/*.html", ["html"]
    gulp.watch sources.sass, ["styles"]
    gulp.watch sources.fonts, ["fonts"]
    gulp.watch sources.images, ["images"]
    gulp.watch sources.vendor, ["vendor"]
    $.util.log($.util.colors.blue("ALL FILES ARE BEING WATCHED (BY THE CIA)."))
    return

