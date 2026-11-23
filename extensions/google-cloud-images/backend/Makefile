project ?=

install:
	python3 -m venv env
	./env/bin/pip install -r requirements.txt

run:
	./env/bin/gunicorn -b :8080 main:app

deploy-dispatch:
	gcloud app deploy \
		-q \
		--project=$(project) \
		dispatch.yaml

deploy:
	gcloud app deploy \
		-q \
		--project=$(project) \
		--version=auto \
		--promote \
		app.yaml
