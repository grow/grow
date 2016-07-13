var browserify = require('browserify');
var buffer = require('vinyl-buffer');
var gulp = require('gulp');
var gutil = require('gulp-util');
var rename = require('gulp-rename');
var sass = require('gulp-sass');
var source = require('vinyl-source-stream');
var uglify = require('gulp-uglify');
var watchify = require('watchify');


var Config = { 
  JS_SOURCES: [
    './js/ui.js'
  ],
  JS_OUT_DIR: './dist/js/',
  JS_OUT_FILE: 'ui.min.js',
  SASS_SOURCE_FORMAT: './sass/**',
  SASS_SOURCE: './sass/ui.sass',
  SASS_OUT_DIR: './dist/css/'
};


function rebundle_(bundler, outdir, outfile, opt_options) {
  var options = opt_options || {};
  return bundler.bundle()
    .on('error', gutil.log.bind(gutil, 'browserify error'))
    .pipe(source(outfile))
    .pipe(buffer())
    .pipe(uglify(options.uglify))
    .pipe(gulp.dest(outdir));
}


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
    rebundle_(bundler, outdir, outfile);
    gutil.log('finished recompiling js');
  });
  return rebundle_(bundler, outdir, outfile, opt_options);
}


gulp.task('compilejs', function() {
    return compilejs(Config.JS_SOURCES, Config.JS_OUT_DIR, Config.JS_OUT_FILE);
});


gulp.task('watchjs', function() {
    return watchjs(Config.JS_SOURCES, Config.JS_OUT_DIR, Config.JS_OUT_FILE);
});


gulp.task('watchcss', function() {
  return gulp.watch(Config.SASS_SOURCE_FORMAT, ['compilecss']);
});


gulp.task('compilecss', function() {
  gulp.src(Config.SASS_SOURCE)
    .pipe(sass({
      outputStyle: 'compressed'
    })).on('error', sass.logError)
    .pipe(rename(function(path) {
      path.basename += '.min';
    }))
    .pipe(gulp.dest(Config.SASS_OUT_DIR));
});


gulp.task('build', ['compilejs', 'compilecss']);
gulp.task('default', ['build', 'watchjs', 'watchcss']);
