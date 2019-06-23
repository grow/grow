var airkit = require('../compilejs');
var gulp = require('gulp');
var config = require('../config');

gulp.task('compilejs', function() {
  return airkit.compilejs(
      config.JS_SOURCES, config.JS_OUT_DIR, config.JS_OUT_FILE,
      config.JS_OPTIONS);
});
