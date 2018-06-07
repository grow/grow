PIP_ENV := $(shell pipenv --venv)

# Default test target for "make test".
# Allows "make test target=grow.pods.pods_test"
target ?= 'grow'

test:
	. $(PIP_ENV)/bin/activate
	$(PIP_ENV)/bin/nosetests \
	  -v \
	  --rednose \
	  --with-coverage \
	  --cover-erase \
		--cover-xml \
	  --cover-package=grow \
	  $(target)

test-pylint:
	. $(PIP_ENV)/bin/activate
	$(PIP_ENV)/bin/pylint --errors-only $(target)
