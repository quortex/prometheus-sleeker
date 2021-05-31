cov:
	pytest --cov-report html --cov=src
serve-cov:
	cd ./htmlcov && python -m http.server 8123
