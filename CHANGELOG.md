# Changelog

## [2.6.0](https://github.com/grow/grow/compare/v2.5.0...v2.6.0) (2026-11-27)


### Features

* **webreview:** inline hardened WebReview client and drop external dependency ([#1273](https://github.com/grow/grow/issues/1273)) ([1e93a29](https://github.com/grow/grow/commit/1e93a29bec75375c9c7abc0d14658741f4670316))


### Documentation

* check in Cloudflare Worker for legacy install.grow.io URLs ([bc1f635](https://github.com/grow/grow/commit/bc1f63551c8dd9918dd4e7b6b86120aaa26754e6))
* host deprecation install.sh on grow.dev for Cloudflare redirects ([8bb5d6d](https://github.com/grow/grow/commit/8bb5d6d6e2397ac758e64f6cae637866d55b32e6))

## [2.5.0](https://github.com/grow/grow/compare/v2.4.0...v2.5.0) (2026-11-23)


### Features

* **docs:** add 8-bit 404 page and harden release workflow ([#1261](https://github.com/grow/grow/issues/1261)) ([9d26694](https://github.com/grow/grow/commit/9d26694c19eee1d6cf2cecba84aebd7b9c59bf9c))
* **docs:** add mobile, Apple touch, and ICO favicons ([#1268](https://github.com/grow/grow/issues/1268)) ([ac17329](https://github.com/grow/grow/commit/ac17329df0bb5d2f69ef641d741d157b120c136f))
* **extensions:** consolidate and harden remaining grow-ext-* packages in monorepo ([#1270](https://github.com/grow/grow/issues/1270)) ([1c22162](https://github.com/grow/grow/commit/1c22162975093bb75b0e2fbcdbe4f2fceb487b77))
* **extensions:** move and harden google-cloud-images in monorepo ([#1269](https://github.com/grow/grow/issues/1269)) ([cb4f602](https://github.com/grow/grow/commit/cb4f6025a7268248149f075024636db9a4c68bd0))


### Bug Fixes

* **ci:** use uv --frozen in docs workflow and update uv.lock ([#1263](https://github.com/grow/grow/issues/1263)) ([60cebce](https://github.com/grow/grow/commit/60cebcecbe0f7000db33f39b25a65bc5d3bdec23))
* **docs:** add scroll-padding-top for sticky header deeplinks ([#1265](https://github.com/grow/grow/issues/1265)) ([812741b](https://github.com/grow/grow/commit/812741b6fd76c33657d80afb85723745be7b68e6))
* **docs:** remove sidebar nav and center body text on 404 page ([#1264](https://github.com/grow/grow/issues/1264)) ([cf24c14](https://github.com/grow/grow/commit/cf24c14c245bb6281ea89971ebc397f3d915f7a7))
* **footer:** open ecosystem links in same tab ([#1267](https://github.com/grow/grow/issues/1267)) ([4359599](https://github.com/grow/grow/commit/4359599e7bf6cb9ca5f3f440b706e17f3c0a4168))


### Documentation

* add pink meta theme-color for mobile ([#1266](https://github.com/grow/grow/issues/1266)) ([217685a](https://github.com/grow/grow/commit/217685a602f7a14f62219d8c16e071f1ecc6143b))

## [2.4.0](https://github.com/grow/grow/compare/v2.3.1...v2.4.0) (2026-11-22)


### Features

* **docs:** achieve 100% Lighthouse scores and add SEO/AEO ([#1258](https://github.com/grow/grow/issues/1258)) ([31c3668](https://github.com/grow/grow/commit/31c3668b101e830a235a06ad0eee3cbbd7512e2c))


### Bug Fixes

* **sitemap:** omit xhtml namespace and alternate links for single-locale sites ([a1648e6](https://github.com/grow/grow/commit/a1648e63e40a5b3f9e8be94d7dcfe50127b68b6b))


### Documentation

* update homepage page title ([#1260](https://github.com/grow/grow/issues/1260)) ([1c9cbe6](https://github.com/grow/grow/commit/1c9cbe663e15f0b43ca97371b75624fee3cda3f8))

## [2.3.1](https://github.com/grow/grow/compare/v2.3.0...v2.3.1) (2026-11-22)


### Bug Fixes

* **docs:** align footer horizontal padding with main docs shell ([#1255](https://github.com/grow/grow/issues/1255)) ([edb3401](https://github.com/grow/grow/commit/edb340121b6e200764d387039fc99b921aaf5b4d))
* **footer:** move PyPI badge into Ecosystem ([#1256](https://github.com/grow/grow/issues/1256)) ([03e92eb](https://github.com/grow/grow/commit/03e92eb9f6f47028ec1c8824d807c4738261afc3))


### Documentation

* add Astro-style global footer ([#1253](https://github.com/grow/grow/issues/1253)) ([7780e1b](https://github.com/grow/grow/commit/7780e1bca1eae5a0579d73c296c90eea063414a4))

## [2.3.0](https://github.com/grow/grow/compare/v2.2.3...v2.3.0) (2026-11-22)


### ⚠ BREAKING CHANGES

* update to node v18 in base image

### Features

* add grow.__version__, lazy-load googleapiclient, modernize error page and dev logs ([a82d7b4](https://github.com/grow/grow/commit/a82d7b49b9d5e30085d9f4754cbf5fc0036322a3))
* **cli:** modernize dev server and build output (Root.js-inspired) ([56389f8](https://github.com/grow/grow/commit/56389f877387b7d5400c2313f0d9ab06f370f16a))
* **docs:** modernize grow.dev UI, drop all vendored JS, and deploy via GitHub Pages ([8622a48](https://github.com/grow/grow/commit/8622a480a1153bb413ac278b051cd8858ffb138d))
* **examples:** add minimal zero-Node Grow starter pod with i18n ([9b50703](https://github.com/grow/grow/commit/9b507034043914b2317987c2150c08ad84950d16))
* **ui:** redesign dev console with search, filters, stats, and modern styling ([9d5a3f4](https://github.com/grow/grow/commit/9d5a3f4df1fee12813e897ca938d398a7e2657bf))
* update to node v18 in base image ([2ef22aa](https://github.com/grow/grow/commit/2ef22aa0be44bf6e3e76c8e1190bb67cd2aee828))


### Bug Fixes

* **docker:** pin NVM_VERSION to avoid unauthenticated GitHub API 403 ([421d607](https://github.com/grow/grow/commit/421d607afeb1a6dc3365fe1e08aca25a75581bad))
* **docs:** add mobile slide-over nav drawer and responsive layout ([659ddf4](https://github.com/grow/grow/commit/659ddf4d21d60e8436f65a8a2cf02f433e7ab6ac))
* **docs:** keep mobile header on a single row ([e6e1cf9](https://github.com/grow/grow/commit/e6e1cf9d2b5eba96ef2bfdae86300ab7ce77f075))
* **docs:** remove redundant backslash escapes before pipes inside table code spans ([181158f](https://github.com/grow/grow/commit/181158f270dfc1312d6501e5537a2f2b1712cddf))
* **i18n:** delegate fuzzy_load to Babel for existing locales (fixes nb/CLDR aliases) ([92bcef4](https://github.com/grow/grow/commit/92bcef46ffbde594a6c981d80672311d39202d88))
* **oauth:** default to localhost callback with free port and clear OOB guidance ([#1248](https://github.com/grow/grow/issues/1248)) ([a20fb94](https://github.com/grow/grow/commit/a20fb943903895718891760dc3b1f485de409145))
* pin dependencies ([7294ccf](https://github.com/grow/grow/commit/7294ccf0b5e4e5807949cd43c76050a6bad48ed0))
* resolve backlog bugs across routing, deploys, OAuth, and translations ([#1247](https://github.com/grow/grow/issues/1247)) ([33a75c0](https://github.com/grow/grow/commit/33a75c08b137552c164cf1bbf20ecc9d47435b7e))
* **security:** harden YAML loading, dev server paths, and zip extraction ([059be18](https://github.com/grow/grow/commit/059be18435270e8840951a3007b5559590064883))
* upgrade Dockerfile to Node 22 and fix docs icons/component styles ([9762600](https://github.com/grow/grow/commit/97626002c141e1ef84079afb5e5108f3551e28a5))


### Performance Improvements

* cache Pod.podspec and Locale validation, use functools.cached_property, lazy-load heavy deps ([27f2f66](https://github.com/grow/grow/commit/27f2f66b23d5e5879d670943a91dda9e5f62d5e7))
* optimize YAML untagging and file storage I/O ([a482aa7](https://github.com/grow/grow/commit/a482aa751c4d1fda8cbfb584d727c9c5227ed857))


### Documentation

* add border outline to mobile drawer navigation tabs ([#1249](https://github.com/grow/grow/issues/1249)) ([81fb7ee](https://github.com/grow/grow/commit/81fb7ee6ad83559dc80b8e85448f1723ca91a4fd))
* add Root.js maintenance banner, reorganize IA, and rewrite core docs ([cf8ce88](https://github.com/grow/grow/commit/cf8ce88f98d8c2196af9931f0de8a09758fd97fd))
* fix sidebar badge sizing, remove stale New banner, and modernize CI/LibYAML docs ([1caaeb0](https://github.com/grow/grow/commit/1caaeb0e859d5dabb6b8a64d85d3935af4e76b23))
* fix syntax highlighting contrast with github-dark and rewrite public API reference ([56300c1](https://github.com/grow/grow/commit/56300c12d9936e110de9f1b585286554211b0199))
* import grow.dev site into monorepo without Node/Gulp/Sass build chain ([8ce205b](https://github.com/grow/grow/commit/8ce205b0828dd000c00747ceee6c9f17a5ba86d6))
* replace 404 starter repo link with grow/grow.dev in README ([f7f0ddc](https://github.com/grow/grow/commit/f7f0ddc5173d0ec1689c5071671906e8b32cf760))
* rewrite README and CONTRIBUTING and consolidate PyPI readme ([4168088](https://github.com/grow/grow/commit/416808807abf7337ede1ec9fe23d15069e8912ff))
* strengthen border outline and contrast on mobile drawer tabs ([#1250](https://github.com/grow/grow/issues/1250)) ([45ad6ac](https://github.com/grow/grow/commit/45ad6acdac5306ba9e1fde20273d816ad433bcfa))
* use pill border-radius on CTA buttons ([#1246](https://github.com/grow/grow/issues/1246)) ([97241f2](https://github.com/grow/grow/commit/97241f2a4c17d42d6136ab75278a88a4cf3d2275))


### Miscellaneous Chores

* deprecate legacy install.py script with migration guidance ([#1251](https://github.com/grow/grow/issues/1251)) ([1024474](https://github.com/grow/grow/commit/1024474e406f23c21d813ff8ff1228d2df77d0b5))

### [2.2.3](https://www.github.com/grow/grow/compare/v2.2.2...v2.2.3) (2022-04-21)


### Bug Fixes

* add instructions to test using pytest ([2f14710](https://www.github.com/grow/grow/commit/2f1471041dba9cf75ceef4a6e8f3f176028986d7))
* correct wrong value of collection.sub_path ([8f84cf7](https://www.github.com/grow/grow/commit/8f84cf77a9ae222b565410310355860dbf6d874c))

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
