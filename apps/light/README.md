# Light Theming

A theming library for ads, landing pages, and future static page generation (e.g. all components)

## Basics

All source files are in `src`

`gulp` is ran, and then

All output files are in `static`

django then reads this directory as a template folder for static page generation

## Install

1. Install [node](http://nodejs.org/)
2. Setup your environment PATH to include "node\_modules/bin"
3. Run `npm install`
4. Run `bower install`
5. Run `gulp <command>`

## Gulp

`gulp dev` to run an autoreload server for development (live css, reload on js + html changes)

## Directory Structure

** Per Client, Product, Theme: **

`src/clients/:client_name/:product/:product-theme/{images,styles,scripts,templates}`

** Shared Resources: **

`src/components/:component/{images,styles,scripts,templates}`

** Output: **

`static/light/:client_name/product/product-theme/{index.html,styles/main.css,images/*}`

## Technology Stack

- [Gulp.js](http://gulpjs.com) - Compilation Framework
- [Bower](http://bower.io) - A module based javascript library
- [Browserify](http://browserify.org) - Compilation of CommonJS Modules
- [BrowerSync](http://browsersync.io) - Live Reload
