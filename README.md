# django-default-project


This is meant as a base template for new Django projects which uses pipenv to manage its 3rd party packages. 
The project comes preconfigured for those packages:
  
    [packages]
    
    django = "*"
    django-secrets = "*"
    django-undeletable = "*"
    django-extensions = "*"
    dj-static = "*"
    django-compressor = "*"
    django-axes = "*"
    django-libsass = "*"
    raven = "*"
    pypugjs = "*"
    
    [dev-packages]
    
    django-debug-toolbar = "*"
    django-livereload-server = "*"
    "flake8" = "*"
    "fabric3" = "*"
    ipdb = "*"

    
      
Furthermore it inclueds a hello world with PUG template, SASS styles and VueJS. 
jQuery and FontAwesome are also included for convenience. The project has a flat settings hirachy so you can do the following:

 1. Alice and Bob set an environment var pointing to their own settings like "settings.bob"
 2. When starting a new project they just have to copy setting/dev.py and change it to their liking
 3. When switching and working on multiple projects, everybody can have their own setting checked into the 
 project and automatically using em without the need to remember to activate "<project_name>.settings.whatever" 
 (influenced by the really cool TwoScoops of Django)
 
 Django-secrets will keep your secrets really secret and help you with your deployment so that you only need to initialize 
 your secret environment variables. Also works super easy with i.e. Travis CI.
 
 Django-axes is not working under 1.11, but i kept it anyways, hoping the functionality will return. :)
 
 All assets and templates are stored in their top level folders .. yes i know its not portable that way, but most of 
 the times i dont build portable apps. I create projects that are meant to be be running at customers and never 
 see the public light and thus they shall be clean without the need to remember which assets are hiden in which subfolders.
 The styles.sass in compiled on the fly and thanks to the wonderful livereload-server changes will be visible right away in
 you browser (as well as code changes to python files).
 
 Once the settings file is fed with the needed credentials all errors (python and javascript) will be catched by 
 Sentry.io for error handling. 
 
 misc/setup_repo.sh will setup the current repo with a flake8 commit hook to always commit clean code only. :D
 wsgi.py is patched with the awesome dj-static lib so you dont neccessarily need to remember to serve static 
 files separately unless you really want to.
 
 Because pipenv didnt work that well in its early stages, there is still a requirements.txt. Have to play a little 
 more with pipenv to be a little more confident to completely switch, but installing a lot of stuff is still a 
 lot faster using plain pip. The Pipfile is a lot better to manage tho. So for now i partly use both.
 
 One more thing: The project template features a ready to use fabfile which will grant you some basic tasks like:
 
   - _fab deploy_ which will push your content and restart uwsgi
   - _fab migrate_ which will push updates, updating packages, migrating the DB, compressing files, collecting 
   static files and finally restart the server for you.
   
 Hope i didnt forget any gem inside .. have fun with this project template!
 
# Installation

    django-admin.py startproject \
    --template=https://github.com/kakulukia/django-default-project/zipball/master \
    <new project name here>
