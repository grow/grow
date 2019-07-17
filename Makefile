PIP_ENV := $(shell pipenv --venv)

# Default test target for "make test".
# Allows "make test target=grow.pods.pods_test"
target ?= 'grow'

# Default test target for "make test". Allows "make target=grow.pods.pods_test test"
coverage ?= false

develop:
	pipenv install --dev

test:
	. $(PIP_ENV)/bin/activate

	@if [ "$(coverage)" == true ]; then \
	$(PIP_ENV)/bin/nosetests \
	  -v \
	  --rednose \
	  --with-coverage \
	  --cover-erase \
		--cover-xml \
	  --cover-package=grow \
	  $(target);\
	else \
		$(PIP_ENV)/bin/nosetests \
			-v \
			--rednose \
			$(target);\
	fi

test-pylint:
	. $(PIP_ENV)/bin/activate
	$(PIP_ENV)/bin/pylint --errors-only $(target)
