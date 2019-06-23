const config = require('../config');
const gulp = require('gulp');
const autoprefixer = require('gulp-autoprefixer');
const rename = require('gulp-rename');
const sass = require('gulp-sass');

gulp.task('sass', function() {
  gulp.src(config.SASS_SOURCE)
      .pipe(sass({
        outputStyle: 'compressed',
      })).on('error', sass.logError)
      .pipe(rename(function(path) {
        path.basename += '.min';
      }))
      .pipe(autoprefixer({
        browsers: [
          'last 2 versions',
          'last 2 iOS versions',
        ],
      }))
      .pipe(gulp.dest(config.SASS_OUT_DIR));
});
