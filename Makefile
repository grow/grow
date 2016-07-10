APT_GET := $(shell command -v apt-get 2> /dev/null)
BREW := $(shell command -v brew 2> /dev/null)

PLATFORM = $(shell uname -s | sed -e 's/Darwin/Mac/')
VERSION=`cat grow/VERSION`
FILENAME="Grow-SDK-$(PLATFORM)-$(VERSION).zip"

GITHUB_USER="grow"
GITHUB_REPO="grow"

export GOPATH := $(HOME)/go/
export PATH := $(HOME)/go/bin/:$(PATH)

# Default test target for "make test". Allows "make target=grow.pods.pods_test test"
target ?= 'grow/'

clean:
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

develop:
	virtualenv env --distribute
	. env/bin/activate
	@pip --version > /dev/null || { \
	  echo "pip not installed. Trying to install pip..."; \
	  sudo easy_install pip; \
	}
	@virtualenv --version > /dev/null || { \
	  echo "virtualenv not installed. Trying to install virtualenv..."; \
	  sudo pip install virtualenv; \
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
	./env/bin/pip install -r requirements-dev.txt
	./env/bin/pip install --upgrade PyYAML==3.10

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
	./gaenv/bin/pip install NoseGAE==0.5.8
	# https://github.com/faisalraja/gaenv/issues/11
	cat requirements.txt > ./gaenv/requirements-gae.txt
	echo "pyasn1-modules>=0.0.5" >> ./gaenv/requirements-gae.txt
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
	$(MAKE) test-nosetests
	$(MAKE) test-gae

upload-pypi: clean
	. env/bin/activate
	$(MAKE) ensure-master
	$(MAKE) test
	git pull origin master
	python setup.py sdist upload
	$(MAKE) clean

upload-github:
	@github-release > /dev/null || { \
	  go get github.com/aktau/github-release; \
	}
	. env/bin/activate
	$(MAKE) ensure-master
	git pull origin master
	$(MAKE) test
	$(MAKE) release
	@if [ github-release info -u $(USER) -r $(REPO) -t $(VERSION) ]; then \
	  echo "Using existing release."; \
	else \
	  echo "Creating new release."; \
	  git tag $(VERSION) && git push --tags;\
	  github-release \
	    release \
	    -u $(USER) \
	    -r $(REPO) \
	    -t $(VERSION) \
	    -n "$(VERSION)" \
	    --draft; \
	fi
	@echo "Uploading: $(FILENAME)"
	github-release \
	  upload \
	  -u $(USER) \
	  -r $(REPO) \
	  -t $(VERSION) \
	  -n "$(FILENAME)" \
	  --file dist/$(FILENAME)

release: clean
	. env/bin/activate
	pyinstaller grow.spec
	chmod +x dist/grow
	cd dist && zip -r $(FILENAME) grow && cd ..
	./dist/grow
	./dist/grow build ./grow/testing/testdata/pod/
	@echo "Built: dist/$(FILENAME)"

ensure-master:
	@if [ `git rev-parse --abbrev-ref HEAD` != "master" ]; then \
	  echo 'Releases must be uploaded from "master".'; \
	  exit 1; \
	fi

install: clean
	python setup.py install

.PHONY: clean develop develop-linux test test-ci test-gae test-nosetests upload-pypi upload-github ensure-master
