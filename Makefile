APT_GET := $(shell command -v apt-get 2> /dev/null)
BREW := $(shell command -v brew 2> /dev/null)

PLATFORM = $(shell uname -s | sed -e 's/Darwin/Mac/')
VERSION = $(shell cat grow/VERSION)
FILENAME = Grow-SDK-$(PLATFORM)-$(VERSION).zip
FILENAME_CI = Grow-SDK-$(subst osx,Mac,$(subst linux,Linux,$(TRAVIS_OS_NAME)))-$(TRAVIS_TAG).zip

GITHUB_USER = grow
GITHUB_REPO = grow

export GOPATH := $(HOME)/go/
export PATH := $(HOME)/go/bin/:$(PATH)

# Default test target for "make test". Allows "make target=grow.pods.pods_test test"
target ?= 'grow/'

develop:
	@pip --version > /dev/null || { \
	  echo "pip not installed. Trying to install pip..."; \
	  sudo easy_install pip; \
	}
	@virtualenv --version > /dev/null || { \
	  echo "virtualenv not installed. Trying to install virtualenv..."; \
	  sudo pip install virtualenv; \
	}
	virtualenv env --distribute
	. env/bin/activate
	@echo "Trying to install libyaml..."
	@if [ $(BREW) ]; then \
	  brew install libyaml || { \
	    echo " Error installing libyaml with brew."; \
	    echo " Try installing from source: http://pyyaml.org/wiki/LibYAML"; \
	  }; \
	elif [ $(APT_GET) ]; then \
	  sudo apt-get install libyaml-dev; \
	else \
	  echo " You must install libyaml from source: http://pyyaml.org/wiki/LibYAML"; \
	fi
	$(MAKE) build-ui
	./env/bin/pip install --upgrade pip
	./env/bin/pip install -r requirements-dev.txt

build-ui:
	@npm --version > /dev/null || { \
	  if [ $(APT_GET) ]; then \
	    echo "npm not installed. Trying to install npm..."; \
	    sudo apt-get -f install -y --no-install-recommends nodejs-legacy npm; \
	  else \
	    echo "npm not installed. You must install npm."; \
	    echo "Try installing via nvm: https://github.com/creationix/nvm" \
	    exit 1; \
	  fi \
	}
	@cd grow/ui; npm install  .
	@cd grow/ui; ./node_modules/gulp/bin/gulp.js build

develop-linux:
	sudo apt-get install \
	  build-essential \
	  libc6 \
	  libffi-dev \
	  libssl-dev \
	  libxml2-dev \
	  libxslt-dev \
	  libyaml-dev \
	  python \
	  python-all-dev zip \
	  python-pip \
	  zip
	sudo pip install --upgrade --force-reinstall pyyaml
	sudo pip install --upgrade pip
	sudo pip install --upgrade six
	$(MAKE) develop

test:
	. env/bin/activate
	./env/bin/nosetests \
	  -v \
	  --rednose \
	  --with-coverage \
	  --cover-erase \
	  --cover-html \
	  --cover-html-dir=htmlcov \
	  --cover-package=grow \
	  $(target)

test-nosetests:
	nosetests \
	  -v \
	  --rednose \
	  --with-coverage \
	  --cover-erase \
	  --cover-html \
	  --cover-html-dir=htmlcov \
	  --cover-package=grow \
	  grow

test-gae:
	virtualenv gaenv --distribute
	. gaenv/bin/activate
	./gaenv/bin/pip install -r requirements-dev.txt
	./gaenv/bin/pip install gaenv
	./gaenv/bin/pip install NoseGAE==0.5.10
	# https://github.com/faisalraja/gaenv/issues/11
	cat requirements.txt > ./gaenv/requirements-gae.txt
	echo "pyasn1-modules>=0.0.8" >> ./gaenv/requirements-gae.txt
	./gaenv/bin/gaenv -r ./gaenv/requirements-gae.txt --lib lib --no-import .
	NOSEGAE=1 ./gaenv/bin/nosetests \
	  -v \
	  --rednose \
	  --with-gae \
	  --nocapture \
	  --nologcapture \
	  --gae-application=./grow/testing/testdata/pod/ \
	  --gae-lib-root=$(HOME)/google_appengine/ \
	  $(target)

test-ci:
	$(MAKE) build-ui
	$(MAKE) test-nosetests
	$(MAKE) test-gae

prep-release:
	$(MAKE) build-ui
	$(MAKE) test

upload-pypi:
	. env/bin/activate
	$(MAKE) ensure-master
	git pull origin master
	$(MAKE) prep-release
	python setup.py sdist upload

upload-github:
	@github-release > /dev/null || { \
	  go get github.com/aktau/github-release; \
	}
	. env/bin/activate
	$(MAKE) ensure-master
	git pull origin master
	$(MAKE) prep-release
	$(MAKE) release
	@if github-release info -u $(GITHUB_USER) -r $(GITHUB_REPO) -t $(VERSION); then \
	  echo "Using existing release."; \
	else \
	  echo "Creating new release."; \
	  git tag $(VERSION) && git push --tags; \
	  github-release \
	    release \
	    -u $(GITHUB_USER) \
	    -r $(GITHUB_REPO) \
	    -t $(VERSION) \
	    -n "$(VERSION)" \
	    --draft; \
	fi
	@echo "Uploading: $(FILENAME)"
	github-release \
	  upload \
	  -u $(GITHUB_USER) \
	  -r $(GITHUB_REPO) \
	  -t $(VERSION) \
	  -n "$(FILENAME)" \
	  --file dist/$(FILENAME)

# https://github.com/grow/grow/issues/302
setup-release:
	make develop
	. env/bin/activate
	./env/bin/pip install git+https://github.com/pyinstaller/pyinstaller.git\#b78bfe530cdc2904f65ce098bdf2de08c9037abb

release:
	. env/bin/activate
	./env/bin/pyinstaller grow.spec
	chmod +x dist/grow
	cd dist && zip -r $(FILENAME) grow && cd ..
	./dist/grow
	./dist/grow build ./grow/testing/testdata/pod/
	@echo "Built: dist/$(FILENAME)"

release-ci:
	pip install git+https://github.com/pyinstaller/pyinstaller.git\#b78bfe530cdc2904f65ce098bdf2de08c9037abb
	pyinstaller grow.spec
	chmod +x dist/grow
	cd dist && zip -r $(FILENAME_CI) grow && cd ..
	./dist/grow
	./dist/grow build ./grow/testing/testdata/pod/
	@echo "Built: dist/$(FILENAME_CI)"

ensure-master:
	@if [ `git rev-parse --abbrev-ref HEAD` != "master" ]; then \
	  echo 'Releases must be uploaded from "master".'; \
	  exit 1; \
	fi

.PHONY: develop develop-linux test test-ci test-gae test-nosetests upload-pypi upload-github ensure-master
