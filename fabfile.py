# coding=utf-8
from fabric.colors import green
from fabric.context_managers import cd
from fabric.operations import get, local, run
from fabric.state import env

env.shell = "/bin/zsh -c"

APP_NAME = "app_name"
# APP_NAME is also used as user and
# password for the database for local systems - get_new_db task

env.path = f"/opt/www/{APP_NAME}"
env.hosts = ["servername"]


# # DEPLOYMENT TARGETS
# # ####################
# def stage():
#     env.environment = "stage"
#     env.hosts = ["servername"]
#     env.gateway = "andy@mamasystems.de"  # if needed


# def live():
#     env.environment = "live"
#     env.hosts = ["servername"]


# T A S K S
# ###########
def deploy_only():
    """Pull all updates from the remote repository."""
    with cd(env.path):
        print(green("updating from repository .."))
        run("git pull")


def clear_cache():
    with cd(env.path):
        print(green("\ndeleting cache .."))
        manage("clear_cache")
        # manage("thumbnail clear_delete_all")


def restart():
    """Restart nginx and the backend worker."""
    print(green("restarting server .."))
    run(f"pm2 restart {APP_NAME}")

    clear_cache()


def deploy():
    deploy_only()
    update_static()

    restart()


def migrate():
    """
    Pull all updates from the remote repository.
    Migrates the database and installs new lib versions from requirements.
    Static files are also collected.
    """
    deploy_only()

    with cd(env.path):
        print(green("updating packages .."))
        # this might cause some trouble: https://github.com/python-poetry/poetry/issues/732
        run("poetry run pip install --upgrade pip setuptools")
        run("poetry install")

        print(green("migrating database .."))
        manage("migrate --noinput")

        update_static()

    restart()


def update_static():
    with cd(env.path):
        print(green("compressing files .."))
        manage("compress -e pug,html --force")
        # manage("compilescss")

        print(green("collecting static files .."))
        manage("collectstatic --noinput")


def manage(command):
    run("poetry run ./manage.py " + command)


def get_new_db():
    users = local('psql -c "\\du"', capture=True)
    if APP_NAME not in users:
        local(f"psql -c \"CREATE USER {APP_NAME} WITH CREATEDB PASSWORD '{APP_NAME}';\"")

    dbs = local('psql -c "\\l"', capture=True)
    if {APP_NAME} in dbs:
        local(f'psql -U {APP_NAME} postgres -c "DROP DATABASE {APP_NAME};"')

    local(f'psql -U {APP_NAME} postgres -c "CREATE DATABASE {APP_NAME};"')

    with cd(env.path):
        run(f"pg_dump -h localhost -U {APP_NAME} --disable-triggers {APP_NAME} >! dump")
        get("dump", "dump")

    local(f"psql -U {APP_NAME} {APP_NAME} -f dump")
