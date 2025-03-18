from .common import *

DEBUG = False


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




ALLOWED_HOSTS = ['127.0.0.1', '.vercel.app']


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",

]

SECRET_KEY = config('DJANGO_SECRET_KEY')

