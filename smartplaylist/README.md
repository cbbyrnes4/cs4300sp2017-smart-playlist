
###Usage
Run All Commands From Root Directory

Build docker with 

`docker-compose build`

Migrate to database with

`docker-compose run frontend python manage.py migrate`

(Optional) Load data with

`docker-compose run frontend python manage.py loaddata db.json`

Build analysis matrices with

`docker-compose run frontend python build_matrices.py`

Fetch songs for the database with

`docker-compose run frontend python populate_db.py`

Launch server with

`docker-compose up -d`

Stop and delete containers with

`docker stop $(docker ps -a -q)`
 
`docker rm $(docker ps -a -q)`


Delete all data with

`docker volume rm $(docker volume ls -q)`
