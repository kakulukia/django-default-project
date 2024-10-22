# django-default-project

#### Django

This is meant as a base template for new Django projects which uses poetry to manage its 3rd party packages.
The project comes preconfigured for those packages:

    [packages]
    django = "*"
    django-secrets = "*"
    django-undeletable = "*"
    django-extensions = "*"
    dj-static = "*"
    django-compressor = "*"
    django-axes = "*"
    sentry-sdk = "*"
    pypugjs = "*"
    django-post-office = "*"
    uwsgidecorators = "*"
    requests = "*"
    pendulum = "*"
    djangorestframework = "*"

    [dev-packages]
    black = "*"
    django-debug-toolbar = "*"
    django-browser-reload = "*"
    fabric = "*"
    ipdb = "*"
    djdt-flamegraph = "*"
    icecream = "*"
    ruff = "*"

Furthermore, this project template includes a hello world with PUG templates, SASS styles and VueJS
showing off a minimal reactive page featuring [chuck norris facts](https://api.chucknorris.io) which made me click reload a few dozen
times while coding this example app. :P

#### Frontend

Here is a list of what's installed for the frontend:

  - [VueJS](https://vuejs.org/v2/guide/) - the base JS framework
  - [sentry](https://docs.sentry.io/quickstart/) - error reporting for the frontend
  - [lodash](https://lodash.com/docs/4.17.5) - the missing javascript functions
  - [axios](https://github.com/axios/axios) - AJAX calls
  - [Buefy](https://buefy.github.io/#/documentation/start) - VueJs UI framework
  mirroring all [Bulma](https://bulma.io/documentation/columns/basics/) features including
  [Material Design Icons](https://materialdesignicons.com/)

This is only recommended as long as you only want to spice up your pages with a lil reactivity, tho.
In case you want to build a more complex frontend, please consider using the Django rest framework and
and start building a dedicated frontend with `vue ui` ([more detailed instructions here](https://cli.vuejs.org/)).
For smaller projects it has proven to be more efficient to have the frontend checked in as a subfolder in the
backend repo so that you always have the matching backend and frontend code together without messing with
version conflicts

#### Settings

Contrary to Django the project has a flat settings hierarchy so you can do the following:

 1. Alice and Bob set an environment var pointing to their own settings like "settings.bob"
 2. When starting a new project they just have to copy setting/dev.py and change it to their liking
 3. When switching and working on multiple projects, everybody can have their own setting checked into the
 project and automatically using em without the need to remember to activate "<project_name>.settings.whatever"
 (influenced by the really cool TwoScoops of Django)

 Django-secrets will keep your secrets really secret and help you with your deployment so that you only
 need to initialize your secret environment variables. Also works super easy with i.e. Travis CI.

 All assets and templates are stored in their top level folders .. yes i know it's not portable that way, but most of the time
 I don't build portable apps. I create projects that are meant to be running at customers and never
 see the public light, and thus they shall be clean without the need to remember which assets are hidden in which sub folders.
 The styles.sass in compiled on the fly and thanks to the wonderful django-browser-reload changes will be visible right away in
 your browser (as well as code changes to python files).

 Once the settings file is fed with the needed credentials all errors (python and javascript) will be caught by
 Sentry.io for error handling.

 #### Clean Code

 There is a pre configured pre-commit configuration, which can be enabled via `pre-commit install --install-hooks`.

 #### Static Files

 wsgi.py is patched with the awesome dj-static lib, so you don't necessarily need to remember to serve static
 files separately unless you really want to.

 #### One more thing: fabfile

The project template features a ready to use fabfile which will grant you some basic tasks like:

   - _fab deploy_ which will push your content and restart uwsgi
   - _fab migrate_ which will push updates, updating packages, migrating the DB, compressing files, collecting
   static files and finally restart the server for you.

 Hope i didn't forget any gem inside .. have fun with this project template!

## Installation

    django-admin.py startproject \
    --template=https://github.com/kakulukia/django-default-project/zipball/master \
    <new project name here>

    cd <repeat the new project name>

    poetry install

PS: You need [poetry](https://github.com/sdispater/poetry) to install this projects requirements.
You can `pip install poetry` if you don't have it already. I really tried pipenv, but it let me down so many times now.

## 1st time deployment

Needed components:

- recent ubuntu or similar server
- nginx
```bash
    sudo apt install nginx
```
- nodejs with the latest lts
```bash
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
    nvm install --lts
```
- pm2 (runs the webservice)
```bash
    npm install pm2 -g
```
- I usually put websited under /opt/www/<project name> and create a virtualenv there
```bash
    sudo mkdir -p /opt/www/<project name>
    sudo chown -R $USER:$USER /opt/www/<project name>
    cd /opt/www/<project name>
```
- install pyenv to manage python versions
```bash
    curl https://pyenv.run | bash
    echo 'export PATH="/home/<your user>/.pyenv/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
    source ~/.bashrc
```
-install the needed build requirements for python
```bash
    sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev python-openssl
```
- install the need python version and set it to be used globally (update it and install poetry)
```bash
    pyenv install 3.12.7
    pyenv global 3.12.7
    pip install -U pip setuptools poetry
```
- direnv will take care of the needed python environment
```bash
    sudo apt install direnv
    echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
    direnv allow
```
- alter the supplied nginx config to your needs and link it to your sites-enabled and restart nginx
```bash
    sudo ln -s /opt/www/<project>/settings/<your config> /etc/nginx/sites-enabled/
    sudo systemctl restart nginx
```
- execute a local dev server to init local secrets (SECRET_KEY, OPEN_AI_API_KEY, etc.)
```bash
    manage.py runserver
```
- test the uwsgi config
```bash
    uwsgi settings/deployment/project.yml
```
- if everything is fine, start the pm2 job and save it as well installing the pm2 startup job
```bash
    cd settings/deployment
    pm2 start project.sh
    pm2 save
    pm2 startup
    cd -
```
- install sass for (offline compression only)
```bash
    npm install -g sass
```
- prepare the django static files
```bash
    manage.py compress -e pug,html --force
    manage.py collectstatic --noinput
```
Now your project should be up and running. If you want to deploy updates to a server, you can use the fabfile.

- optionally deploy an SSL certificate via certbot
```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx
```
