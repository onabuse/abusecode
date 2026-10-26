.PHONY: install css run dev docker

install:
	pip install -r requirements.txt
	npm install

css:
	npm run build:css

run:
	./run.sh

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker:
	docker build -t abusecode-router .
	docker run --rm -p 8000:8000 -v $$(pwd)/data:/app/data abusecode-router
