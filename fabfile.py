# coding=utf-8
from fabric.context_managers import cd
from fabric.state import env
from fabric.operations import run
from huepy import green

PROJECT_PATH = "/project/path/here"
env.hosts = [
    # 'host.here.com'
]


# T A S K S
# =========
def deploy_only():
    """ Pull all updates from the remote repository. """
    with cd(PROJECT_PATH):
        print(green("updating from repository .."))
        run("git pull")


def restart():
    """ Restart nginx and the backend worker. """
    print(green("restarting server .."))
    run("sudo service uwsgi restart")


def deploy():
    deploy_only()
    restart()


def migrate():
    """
    Pull all updates from the remote repository.
    Migrates the database and installs new lib versions from requirements.
    Static files are also collected.
    """
    deploy_only()
    with cd(PROJECT_PATH):
        print(green("updating packages .."))
        run("pipenv sync")

        print(green("migrating database .."))
        manage("migrate --noinput")

        print(green("compressing files .."))
        manage("compress --force -e pug")

        print(green("collecting static files .."))
        manage("collectstatic --noinput")

    restart()


def manage(command):
    run("pipenv run manage.py " + command)
