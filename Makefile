all: schema format

schema:
	python botoy/_internal/models/schemas/generate.py

format:
	python -m black .
	python -m isort .
