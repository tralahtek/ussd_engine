
test:
	@docker-compose run --service-port app python manage.py test

base_image:
	docker build -t  mwaaas/django_ussd_airflow:base_image -f BaseDockerfile .
	docker push mwaaas/django_ussd_airflow:base_image

compile_documentation:
	docker-compose run app make -C /usr/src/app/docs html

create_dynamodb_table:
	docker-compose run ansible ./create_dynamodb.sh

deploy:
	docker run -e VERSION=$(version) -e PYPI_PASSWORD=$(PYPI_PASSWORD) -e PYPI_USER=$(PYPI_USER) -v '$(PWD):/usr/src/app' mwaaas/dev_tool_pypi:latest ussd/__init__.py
