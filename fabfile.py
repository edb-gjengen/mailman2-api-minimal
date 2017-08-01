from contextlib import contextmanager as _contextmanager
from fabric.api import run, sudo, env, cd, prefix

env.use_ssh_config = True
env.hosts = ['lynx.neuf.no']
env.project_path = '/var/www/neuf.no/mailman2-api-minimal'
env.user = 'gitdeploy'
env.activate = 'source {}/venv/bin/activate'.format(env.project_path)


@_contextmanager
def virtualenv():
    with cd(env.project_path), prefix(env.activate):
        yield


def deploy():
    with virtualenv():
        run('git pull')  # Get source
        run('pip install -r requirements.txt')  # install deps in virtualenv

    # Reload mxapi.neuf.no
    sudo('/usr/bin/supervisorctl pid mailman-api.neuf.no | xargs kill -HUP', shell=False)
