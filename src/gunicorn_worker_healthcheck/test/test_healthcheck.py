from time import sleep
import contextlib
import importlib.resources
import pytest
import requests
import socket
import subprocess
import sys


def random_port():
    s = socket.socket()
    with contextlib.closing(s):
        s.bind(('localhost', 0))
        return s.getsockname()[1]


@pytest.fixture()
def server(tmp_path):
    main = random_port()
    check = random_port()

    config = importlib.resources.files(__package__).joinpath(
        'fixture/conf.py').open('r').read()
    (tmp_path / 'gunicorn.conf.py').write_text(
        config.format(main=main, check=check))
    proc = subprocess.Popen(
        [sys.executable, '-m', 'gunicorn',
         'gunicorn_worker_healthcheck.test.fixture.app:wsgi'],
        cwd=str(tmp_path))
    yield {'main': main, 'check': check}
    proc.terminate()
    proc.wait(5)


def test_runs_healthcheck_on_separate_port(server):
    http = requests.Session()
    timeout = 10
    for _ in range(timeout):
        sleep(1)
        r = http.get('http://localhost:%s' % server['check'])
        if r.status_code == 200:
            assert r.text.strip() == '2 workers ready'
            r = http.get('http://localhost:%s' % server['main'])
            assert r.status_code == 200
            assert r.text.strip() == 'OK'
            break
    else:
        pytest.fail(f'Did not start inside {timeout} seconds')
