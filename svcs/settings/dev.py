from .common import *


tmpPostgres = urlparse(os.getenv("DATABASE_URL"))


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmpPostgres.path.replace('/', ''),
        'USER': tmpPostgres.username,
        'PASSWORD': tmpPostgres.password,
        'HOST': tmpPostgres.hostname,
        'PORT': 5432,
        'TEST': {
            'NAME': 'test_neondb_unique'
        }
    },

}


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",

]
SECRET_KEY = 'django-insecure-s%toq7wi0frjk-p3@k=)#4@7^h$di&o%77n5ya^)h9hbkb8*_5'

DEBUG = True

ALLOWED_HOSTS = ['*']