#!/bin/bash

command -v virtualenv >/dev/null 2>&1 || { echo >&2 "Install VirtualEnv"; pip install virtualenv;}

if [ ! -r ../venv ]; then
	echo "Creating VirtualEnv"
	virtualenv ../venv
	source ../venv/bin/activate
	cd smartplaylist
	pip install -r requirements.txt
	python -m nltk.downloader punkt
	cd ..
	deactivate
fi
export DJANGO_SETTINGS_MODULE="mysite.settings"
export POSTGRES_DATABASE="postgres"
export POSTGRES_USER="smartplaylist"
export POSTGRES_PASSWORD="smartplaylist_db_password"
export DB_IP="localhost"
docker-compose build
docker-compose up -d db
source ../venv/bin/activate
cd smartplaylist
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
echo "Environment Ready For Use"
