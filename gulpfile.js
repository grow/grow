require('es6-promise').polyfill();
require('require-dir')('./gulp/tasks');
var gulp = require('gulp');

gulp.task('build', ['sass', 'compilejs']);
gulp.task('default', ['sass', 'watch']);
