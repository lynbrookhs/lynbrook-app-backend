## Getting Started
This how you can run your own version of lynbrook app backend with your own test user

### Prerequisites

- Install [Docker]("https://docs.docker.com/get-docker/") [Docker-compose]("https://docs.docker.com/compose/install/")

### Changing settings.py
 - comment or remove google auth and storage
```python
SOCIAL_AUTH_GOOGLE_KEY = os.environ["GOOGLE_API_KEY"]
SOCIAL_AUTH_GOOGLE_SECRET = os.environ["GOOGLE_API_SECRET"]
SOCIAL_AUTH_SCHOOLOGY_KEY = os.environ["SCHOOLOGY_API_KEY"]
SOCIAL_AUTH_SCHOOLOGY_SECRET = os.environ["SCHOOLOGY_API_SECRET"]
...
```
```python
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_BUCKET_NAME = "lynbrook-app"
GS_PROJECT_ID = "lynbrook-high"
GS_CREDENTIALS = Credentials.from_service_account_file(os.environ["GCS_CREDS"])
GS_DEFAULT_ACL = "authenticatedRead"
GS_FILE_OVERWRITE = False
...
```

### Compile new Requirements.txt
```bash
poetry export -f requirements.txt --output requirements.txt
```

### Django Stuff

You can learn more about the django [here]("https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django")

#### Make Migrations
```
docker-compose run web /code/manage.py makemigrations
```

```
docker-compose run web /code/manage.py migrate
```
#### Create test user
```
docker-compose run web /code/manage.py  createsuperuser  --email=your@email.here
```
###

### Run server
```
docker-compose up
```

[You can also setup debugging using docker on vscode]("https://code.visualstudio.com/docs/containers/docker-compose")