def wsgi(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/plain; charset=ascii')])
    return ['OK\n'.encode('ascii')]
