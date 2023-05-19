from glob import glob
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
import os
import logging
import threading


__version__ = '1.0.0'


def start(cfg):
    bind = cfg.get('healthcheck_bind')
    if not bind:
        return

    check = HealthCheck(
        bind,
        cfg.get('healthcheck_directory', ''),
        cfg.get('healthcheck_filename', '.gunicorn.worker.{}'),
        cfg.get('healthcheck_require_workers', 1))
    check.register(cfg)
    check.start()


class HealthCheck(threading.Thread):

    def __init__(self, bind, directory, filename, workers):
        self.bind = bind
        self.directory = directory
        self.filename = filename
        self.workers = workers

        WSGIRequestHandler.log_request = lambda *args: None  # sigh
        host, port = self.bind.split(':')
        self.server = WSGIServer((host, int(port)), WSGIRequestHandler)
        self.server.set_app(self.wsgi_app)

        super().__init__(daemon=True, target=self.server.serve_forever)

    def register(self, cfg):
        cfg['when_ready'] = self.log_port
        cfg['post_worker_init'] = self.add_worker
        cfg['worker_exit'] = self.remove_worker
        cfg['on_exit'] = self.stop

    def log_port(self, server):
        logging.getLogger('gunicorn.error').info(
            'Healthcheck listening at: http://%s', self.bind)

    def add_worker(self, worker):
        open(self.pidfile(worker.pid), 'w').close()

    def remove_worker(self, worker, server):
        f = self.pidfile(worker.pid)
        if os.path.exists(f):
            os.remove(f)

    def pidfile(self, name):
        return os.path.join(self.directory, self.filename.format(name))

    def stop(self, server):
        for f in glob(self.pidfile('*')):
            os.remove(f)

        self.server.shutdown()
        self.server.server_close()
        self.join(1)

    def wsgi_app(self, environ, start_response):
        count = len(list(glob(self.pidfile('*'))))
        if count >= self.workers:
            status = '200 OK'
        else:
            status = '500 Internal Server Error'
        start_response(status, [('Content-type', 'text/plain; charset=ascii')])
        return [f'{count} workers ready\n'.encode('ascii')]
