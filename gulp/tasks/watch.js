var airkit = require('../compilejs');
var gulp = require('gulp');
var config = require('../config');

gulp.task('watch', function() {
  gulp.watch(config.SASS_SOURCE, ['sass']);
  return airkit.watchjs(
      config.JS_SOURCES, config.JS_OUT_DIR, config.JS_OUT_FILE,
      config.JS_OPTIONS);
});
