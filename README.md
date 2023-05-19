# gunicorn_worker_healthcheck

HTTP endpoint that counts ready gunicorn workers

When using the default `sync` gunicorn worker, using an HTTP endpoint of the application itself
(i.e. that is also handled by the same mechanism, namely the gunicorn workers, as normal application traffic)
to check whether the application is able to handle traffic
(and to e.g. remove it from the load balancing rotation on failure)
can lead to negative feedback loops in high load situations:

The workers may become so backed up with application requests that they are unable to respond to the healthcheck requests in a timely manner.
Thus, this application is removed from serving traffic, 
leaving even less applications to serve the incoming traffic,
thus increasing the chance that they, too, will become backed up 
-- repeat until no applications are available for serving traffic at all.

This package provides an alternative healthcheck endpoint that 
a) is served by a separate thread, independent of the main application traffic
b) only checks whether the application and gunicorn startup process has completed
(i.e. any/all gunicorn worker processes have reported to be ready).


## Usage

Put this into your config file (usually `gunicorn.conf.py`):

```
import gunicorn_worker_healthcheck

healthcheck_bind = '127.0.0.1:8001'
gunicorn_worker_healthcheck.start(globals())
```

This starts an HTTP server in a thread; 
on request it counts the number of workers that have notified they are ready
(using the [`post_worker_init` hook](https://docs.gunicorn.org/en/latest/settings.html#post-worker-init) to write a pid file).
If the required number of workers are ready, it returns HTTP 200, else 500.


## Configuration

* `healthcheck_bind` host:port on which to listen for healthcheck requests (default: None, i.e. healthcheck is disabled)
* `healthcheck_require_workers` count of workers that must be ready for the healthcheck to report success (default: 1)
* `healthcheck_directory` directory in which to store the state files, one per worker (default: `''`, i.e. the current directory)
* `healthcheck_filename` format string how to name the state files, must contain one placeholder `{}` for the pid (default: `'.gunicorn.worker.{}'`)
