.PHONY: install dev build publish package-install start lint

install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

build:
    make install
    ./build.sh

publish:
	poetry publish --dry-run

package-install:
	poetry build
    python3 -m pip install dist/*.whl

lint:
	poetry run flake8

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app