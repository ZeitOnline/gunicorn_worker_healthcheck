bind = '127.0.0.1:{main}'
healthcheck_bind = '127.0.0.1:{check}'

workers = 2

import gunicorn_worker_healthcheck
gunicorn_worker_healthcheck.start(globals())
