var airkit = require('airkit/gulp/compilejs');
var gulp = require('gulp');
var sass = require('gulp-sass');
var rename = require('gulp-rename');

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

gulp.task('compilejs', function() {
    return airkit.compilejs(Config.JS_SOURCES, Config.JS_OUT_DIR, Config.JS_OUT_FILE);
});

gulp.task('watchjs', function() {
    return airkit.watchjs(Config.JS_SOURCES, Config.JS_OUT_DIR, Config.JS_OUT_FILE);
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
