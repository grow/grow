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

# Default test coverage for "make test".
coverage ?= false

develop:
	@pip --version > /dev/null || { \
	  echo "pip not installed. Trying to install pip..."; \
	  sudo easy_install pip; \
	}
	@pipenv --version > /dev/null || { \
	  echo "pipenv not installed. Trying to install pipenv..."; \
	  sudo pip install pipenv; \
	}
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
	pipenv update
	pipenv install --dev
	$(MAKE) build-ui

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
	@cd grow/ui; yarn install
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
	$(MAKE) develop

pylint:
	pipenv run pylint --errors-only $(target)

test:
	@if [ "$(coverage)" = true ]; then \
		pipenv run nosetests \
		  -v \
		  --rednose \
			--with-coverage \
			--cover-erase \
			--cover-xml \
			--cover-package=grow \
		  $(target);\
	else \
		pipenv run nosetests \
			-v \
			--rednose \
			$(target);\
	fi

test-nosetests:
	pipenv run nosetests \
	  -v \
	  --rednose \
	  --with-coverage \
	  --cover-erase \
		--cover-xml \
	  --cover-package=grow \
	  grow

test-pylint:
	pipenv run pylint --errors-only $(target)

test-circle:
	$(MAKE) build-ui
	$(MAKE) test-nosetests
	$(MAKE) test-pylint

prep-release:
	$(MAKE) build-ui
	$(MAKE) test

upload-pypi:
	# TODO: While on branch for python 3 this doesn't work.
	# $(MAKE) ensure-master
	# git pull origin master
	$(MAKE) prep-release
	python setup.py sdist bdist_wheel
	pip3 install urllib3[secure] --upgrade
	pip3 install twine --upgrade
	# twine upload dist/grow-$(VERSION)*
	# TODO: Using temporary crazy version numbers.
	twine upload dist/grow-1.0.0a*

ensure-master:
	@if [ `git rev-parse --abbrev-ref HEAD` != "master" ]; then \
	  echo 'Releases must be uploaded from "master".'; \
	  exit 1; \
	fi

.PHONY: develop develop-linux test test-ci test-nosetests upload-pypi upload-github ensure-master
