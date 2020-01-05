version_file=./ussd/version.py
report_coverage_command="bash <(curl -s https://codecov.io/bash) && python-codacy-coverage -r coverage.xml"
dev_tools=docker run -e PYPI_PASSWORD=$(PYPI_PASSWORD) -e PYPI_USER=$(PYPI_USER) -v '$(PWD):/usr/src/app' mwaaas/dev_tool_pypi:latest

use_cov=no
report_cov=no

coverage_command := $(shell [ $(use_cov) = yes ] && echo "coverage run --omit=*test*,*ven* " || echo "python" )
report_coverage_command := $(shell [ $(report_cov) = yes ] && echo " && bash <(curl -s https://codecov.io/bash) && python-codacy-coverage -r coverage.xml" || echo )

python_unittest_command = -m unittest discover

test_command = $(coverage_command) $(python_unittest_command) $(report_coverage_command)

test:
	@echo '$(test_command)'
	@docker-compose run --service-port app bash -c '$(test_command)'

base_image:
	docker build -t  mwaaas/django_ussd_airflow:base_image -f BaseDockerfile .
	docker push mwaaas/django_ussd_airflow:base_image

compile_documentation:
	docker-compose run app make -C /usr/src/app/docs html

create_dynamodb_table:
	docker-compose run ansible ./create_dynamodb.sh

deploy:
	$(dev_tools) set_version $(version_file) $(version)
	docker-compose run app python setup.py sdist
	$(dev_tools) publish
	$(dev_tools) reset_version $(version_file)
