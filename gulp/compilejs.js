var babelify = require('babelify');
var browserify = require('browserify');
var buffer = require('vinyl-buffer');
var gulp = require('gulp');
var gutil = require('gulp-util');
var source = require('vinyl-source-stream');
var stringify  = require("stringify");
var uglify = require('gulp-uglify');
var watchify = require('watchify');


/**
 * Compiles js code using browserify and uglify.
 * @param {Array.<string>} sources List of JS source files.
 * @param {string} outdir Output directory.
 * @param {string} outfile Output file name.
 * @param {Object=} opt_options Options.
 */
function compilejs(sources, outdir, outfile, opt_options) {
  var bundler = browserify({
    entries: sources,
    debug: false
  });
  return rebundle_(bundler, outdir, outfile, opt_options);
}


/**
 * Watches JS code for changes and triggers compilation.
 * @param {Array.<string>} sources List of JS source files.
 * @param {string} outdir Output directory.
 * @param {string} outfile Output file name.
 * @param {Object=} opt_options Options.
 */
function watchjs(sources, outdir, outfile, opt_options) {
  var bundler = watchify(browserify({
    entries: sources,
    debug: false,
    // Watchify options:
    cache: {},
    packageCache: {},
    fullPaths: true
  }));

  bundler.on('update', function() {
    gutil.log('recompiling js...');
    rebundle_(bundler, outdir, outfile, opt_options);
    gutil.log('finished recompiling js');
  });
  return rebundle_(bundler, outdir, outfile, opt_options);
}


function rebundle_(bundler, outdir, outfile, opt_options) {
  var options = opt_options || {};
  return bundler
    .transform("babelify", {presets: ["@babel/preset-env"]})
    .transform(stringify, {
      appliesTo: { includeExtensions: ['.html'] },
      minify: true,
    })
    .bundle()
    .on('error', gutil.log.bind(gutil, 'browserify error'))
    .pipe(source(outfile))
    .pipe(buffer())
    .pipe(uglify(options.uglify))
    .pipe(gulp.dest(outdir));
}


module.exports = {
  compilejs: compilejs,
  watchjs: watchjs
};
