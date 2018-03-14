var extend = require('deep-extend');
var fs = require('fs');
var gulp = require('gulp');
var gulpAutoprefixer = require('gulp-autoprefixer');
var path = require('path');
var readdirRecursive = require('fs-readdir-recursive');
var rename = require('gulp-rename');
var sass = require('gulp-sass');
var webpack = require('webpack');
var webpackStream = require('webpack-stream');
var WebpackBabiliPlugin = require("babili-webpack-plugin");

var config = {
  JS_SOURCE_DIR: './js/composite/',
  JS_SOURCES: [
    './admin/partials/**/*.js',
    './js/composite/**/*.js',
  ],
  JS_OUT_DIR: './dist/js/',
  JS_OPTIONS: {
    uglify: {
      mangle: false
    }
  },
  SASS_SOURCE_DIR: './sass/composite/**/*.sass',
  SASS_SOURCES: [
    './admin/partials/**/*.sass',
    './sass/composite/**/*.sass',
  ],
  SASS_OUT_DIR: './dist/css/'
};

var jsFiles = readdirRecursive(config.JS_SOURCE_DIR);
var entry = {};
jsFiles.forEach(function (value) {
  if (value.endsWith('.js')) {
    var key = value.substring(0, value.length - 3);
    entry[key] = config.JS_SOURCE_DIR + value;
  }
});

var webpackConfig = {
  entry: entry,
  mode: 'development',
  output: {
    path: path.resolve(__dirname, config.JS_OUT_DIR),
    filename: '[name].min.js'
  }
};
var webpackProdConfig = extend({
  mode: 'production',
}, webpackConfig);

gulp.task('compile-js', function() {
  return gulp.src(config.JS_SOURCES)
      .pipe(webpackStream(
        webpackProdConfig, webpack
      ))
      .pipe(gulp.dest(config.JS_OUT_DIR));
});

gulp.task('watch-js', () => {
  webpackConfig.watch = true;

  gulp.src(config.JS_SOURCES)
    .pipe(webpackStream(
      webpackConfig, webpack
    ))
    .pipe(gulp.dest(config.JS_OUT_DIR));
});

gulp.task('compile-sass', function() {
  gulp.src(config.SASS_SOURCE_DIR)
  .pipe(sass({
    outputStyle: 'compressed'
  })).on('error', sass.logError)
  .pipe(rename(function(path) {
    path.basename += '.min';
  }))
  .pipe(gulpAutoprefixer({
    browsers: [
      'last 1 version',
      'last 2 iOS versions'
    ],
  }))
  .pipe(gulp.dest(config.SASS_OUT_DIR));
});

gulp.task('watch-sass', function() {
  gulp.watch(config.SASS_SOURCES, ['compile-sass']);
});

gulp.task('build', ['compile-js', 'compile-sass']);
gulp.task('grow-build', ['compile-js', 'compile-sass']);
gulp.task('default', ['watch-js', 'watch-sass']);
