# coding=utf-8
from fabric.context_managers import cd
from fabric.state import env
from fabric.operations import run
from fabric.colors import green

PROJECT_PATH = '/project/path/here'
env.hosts = [
    # 'host.here.com'
]


# T A S K S
# =========
def deploy_only():
    """ Pull all updates from the remote repository. """
    with cd(PROJECT_PATH):
        print(green('updating from repository ..'))
        run('git pull')


def restart():
    """ Restart nginx and the backend worker. """
    print(green('restarting server ..'))
    run('sudo service uwsgi restart')


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
        print(green('updating packages ..'))
        run('/home/andy/.virtualenvs/bda/bin/pip install -r requirements.txt --upgrade')

        print(green('migrating database ..'))
        manage('migrate --noinput')

        print(green('compressing files ..'))
        manage('compress --force -e pug')

        print(green('collecting static files ..'))
        manage('collectstatic --noinput')

    restart()


class Colors:
    """
    Colors class:
        reset all colors with colors.reset
        two subclasses fg for foreground and bg for background.
        use as colors.subclass.colorname.
        i.e. colors.fg.red or colors.bg.green
        also, the generic bold, disable, underline, reverse, strikethrough,
        and invisible work with the main class
        i.e. colors.bold
    """
    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strike_through = '\033[09m'
    invisible = '\033[08m'

    class FG:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        light_grey = '\033[37m'
        dark_grey = '\033[90m'
        light_red = '\033[91m'
        light_green = '\033[92m'
        yellow = '\033[93m'
        light_blue = '\033[94m'
        pink = '\033[95m'
        light_cyan = '\033[96m'

    class BG:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        light_grey = '\033[47m'


def manage(command):
    run('pipenv run manage.py ' + command)
