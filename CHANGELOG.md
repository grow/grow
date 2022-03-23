# Changelog

### [2.2.2](https://www.github.com/grow/grow/compare/v2.2.1...v2.2.2) (2022-03-23)


### Bug Fixes

* add supportsAllDrives and supportsTeamDrives to Google files API requests ([b959b1f](https://www.github.com/grow/grow/commit/b959b1fa89fbf71bc3607d7937f2c2c5d2c0ed16))

### [2.2.1](https://www.github.com/grow/grow/compare/v2.2.0...v2.2.1) (2022-03-05)


### Bug Fixes

* pin markupsafe dep ([f3049dd](https://www.github.com/grow/grow/commit/f3049dd2e4dc18a174ddd6493fca9793ae60b5af))

## [2.2.0](https://www.github.com/grow/grow/compare/v2.1.3...v2.2.0) (2022-03-05)


### Features

* add exclude_paths option to translations filter ([ce0ae69](https://www.github.com/grow/grow/commit/ce0ae694518ca5f6d2c2550390ca9cfd206d5796))

### [2.1.3](https://www.github.com/grow/grow/compare/v2.1.2...v2.1.3) (2022-02-08)


### Bug Fixes

* finding git repo root when project is in a subdirectory ([dfa971f](https://www.github.com/grow/grow/commit/dfa971fb0dab26c3a9259346663aa5f765e2f8d4))

### [2.1.2](https://www.github.com/grow/grow/compare/v2.1.1...v2.1.2) (2022-01-12)


### Bug Fixes

* Properly tag release containers on release please releases. ([3dc3fa8](https://www.github.com/grow/grow/commit/3dc3fa82d4208e70c63f54bbe73e8ac3a04c07e8))

### [2.1.1](https://www.github.com/grow/grow/compare/v2.1.0...v2.1.1) (2022-01-12)


### Bug Fixes

* Provide loader explicitly with yaml loading of configuration files. ([66a7e70](https://www.github.com/grow/grow/commit/66a7e7037a8d213705b2c4127648996ffa4b9372))

## [2.1.0](https://www.github.com/grow/grow/compare/v2.0.6...v2.1.0) (2021-09-16)


### Features

* add --ci flag to grow install ([f004a40](https://www.github.com/grow/grow/commit/f004a40967b57c36e06460367354e94aeb3edcce))

### [2.0.6](https://www.github.com/grow/grow/compare/v2.0.5...v2.0.6) (2021-09-06)


### Bug Fixes

* add /ext/ to sys.path for importing from local dirs [#1179](https://www.github.com/grow/grow/issues/1179) ([3e1ef7e](https://www.github.com/grow/grow/commit/3e1ef7e9227e2b4241c2a6886d4dc9ab016627dc))

### [2.0.5](https://www.github.com/grow/grow/compare/v2.0.4...v2.0.5) (2021-08-21)


### Bug Fixes

* ignore extensions in file watchers ([0ecc2f1](https://www.github.com/grow/grow/commit/0ecc2f116bd13685481baa7acb33ed9161556342))
* release package name ([d225edd](https://www.github.com/grow/grow/commit/d225edd3ad7df96df6b05491f032c5caf9fc7e9c))
* remove logic from error handler to increase fault tolerance ([eb3944f](https://www.github.com/grow/grow/commit/eb3944f204116d83861462229a0bc353487902e0))

### [2.0.4](https://www.github.com/grow/grow/compare/v2.0.3...v2.0.4) (2021-08-20)


### Miscellaneous Chores

* release 2.0.4 ([d539fe3](https://www.github.com/grow/grow/commit/d539fe3422189738c3e697166046039a8513f452))

### [2.0.3](https://www.github.com/grow/grow/compare/v2.0.2...v2.0.3) (2021-08-20)


### Miscellaneous Chores

* release 2.0.3 ([fe05e6f](https://www.github.com/grow/grow/commit/fe05e6fa2c6ffcd77f232d954116315647553b99))

### [2.0.2](https://www.github.com/grow/grow/compare/v2.0.1...v2.0.2) (2021-08-18)


### Miscellaneous Chores

* release 2.0.2 ([680658c](https://www.github.com/grow/grow/commit/680658c8764ad40cdbc660ff505834083ffa2141))

### [2.0.1](https://www.github.com/grow/grow/compare/v2.0.0...v2.0.1) (2021-08-18)


### Bug Fixes

* import path for extensions ([391b75e](https://www.github.com/grow/grow/commit/391b75e75621fb5dc76507fe113d263697de45fd))
* markdown dependency ([01e3c5b](https://www.github.com/grow/grow/commit/01e3c5b7d979e2b923b42f48518d0240c3daab1f))


### Documentation

* update readme ([976da63](https://www.github.com/grow/grow/commit/976da63a1d6a2fe7041626412dc71da680e5a805))

## [2.0.0](https://www.github.com/grow/grow/compare/v1.0.4...v2.0.0) (2021-08-18)


### ⚠ BREAKING CHANGES

* remove management commands (use pipenv instead)

### Bug Fixes

* avoid exiting the server when encountering errors on startup ([c22f3ff](https://www.github.com/grow/grow/commit/c22f3ffdd9d499d20971f56fbf0321594cd2d342))


### Code Refactoring

* remove management commands (use pipenv instead) ([f0686a4](https://www.github.com/grow/grow/commit/f0686a43cb668c85db657867eb87215c3da330e0))


### Documentation

* update contributing ([4c0522a](https://www.github.com/grow/grow/commit/4c0522aed91c61322a402ee1facedcade5e904cb))
