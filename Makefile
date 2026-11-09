.PHONY: install etl dashboard test docker docker-down

install:
	pip install -r requirements.txt

etl:
	python -m src.etl.pipeline

dashboard:
	streamlit run app/app.py

test:
	pytest -q

docker:
	docker compose up --build

docker-down:
	docker compose down
