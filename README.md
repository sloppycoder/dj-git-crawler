## Git crawler

This application retrieve the git repositories from gitlab server, and scan through the commits in each repository and store the database in a PostgreSQL database for analysis.
It's written in Python and uses [Django Admin](https://docs.djangoproject.com/en/3.1/ref/contrib/admin/) is the main interface, and [Celery](https://docs.celeryproject.org/en/stable/getting-started/introduction.html) the the engine to execute jobs in background.

## Requirements
To run this application, an external PostgreSQL and Redis serer are required.

## Quick start
step 1: Create a new database and application user. e.g.
```
create user gitcrawler with encrypted password 'gitcrawler';

create database gitcrawler;
grant all privileges on database gitcrawler to gitcrawler;
```
step 2: Create an access token for accessing Gitlab private repositories.
step 3: Create a ".env" file with the following content,
```
# one way to generate the secret is to run a command like
# tr -dc 'a-z0-9!@#$%^&*(-_=+)' < /dev/urandom | head -c50

DJANGO_SECRET="some_random_stuff"
PG_HOST=your_database_host
PG_PORT=yoour_data_port
PG_USERNAME=database_user
PG_PASSWORD=database_password
PG_DATABASE=database_name
DEBUG_MODE=0
REDIS_URI=redis://<redis_host>:<redis_port>
KEY_PASSWORD=dtWqGZiVWi964R
```
step 4: Run this application from an existing docker image
```
./run
```        
step 5: Login and look aroud at ```http://127.0.0.1:8000```
step 6: before run indexing on any repository, please add public key file [root/ssh/id_rsa](root/ssh/id_rsa.pub) to the git server. http authentication is not supported at the moment.         

## Develop and run without using Docker
Install Python 3.8, create virtualenv and install dependencies
```
# assume you have python 3.8 and pip already
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# use dev server or gunicorn to run the application
# consult Procfile to see how to start flower and celery worker
python manage.py runserver
```

## Replace private key and build new docker images
The private key in ```root/ssh``` directory is copied into the container image at build time. When container runs, the [entrypoint.sh](entrypoint.sh) scripts decrypt it using the value of KEY_PASSWORD env var and save it to id_rsa, thus this private key is accessible to anyone who can get into the container at runtime. 
Following the steps below to generate a new key pair:
```
# generate new keypair
ssh-keygen -t rsa -b 2048

# create a new key password, don't loose it once it's generated
export KEY_PASSWORD=$(tr -dc 'a-z0-9!@#$%^&*(-_=+)' < /dev/urandom | head -c16)
openssl enc -aes-256-cbc -pbkdf2  -in id_rsa  -out id_rsa.enc -k $KEY_PASSWORD

# the encrypted key will be in id_rsa.enc file
# it will be copied into container image during build
docker build -t <your image name>:<your_tag> .

# don't forget to update your .env file 

```

## Deploy using systemd
Folllow [instructions here](deploy/systemd/README.md) to deploy the processes using systemd user mode.

## Development
More to come, please watch this space. 

