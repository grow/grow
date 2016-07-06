develop:
	virtualenv env --distribute && \
	. env/bin/activate && \
	pip install -r requirements.txt

test:
	. env/bin/activate && \
	nosetests \
	  -v \
	  --rednose \
	  --with-coverage \
	  --cover-erase \
	  --cover-html \
	  --cover-html-dir=htmlcov \
	  --cover-package=grow \
	  grow/

dist_pypi:
	if [ `git rev-parse --abbrev-ref HEAD` != "master" ]; then
	  echo 'Releases must be made from "master".'
	  exit 1
	fi

dist_github:
	./
