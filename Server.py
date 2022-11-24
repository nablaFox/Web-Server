from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import HTTPStatus
from Interpreter import Interpreter
import os, sys

ROUTES = {}
ROUTES_ERRORS = {
    'Error Document 404' : 404,
    'Error Document 501' : 501
}

def create_routes():
    try:
        with open('.htaccess', 'r') as reader:
            read = reader.read().splitlines()
        for row in range(len(read)):
            key, value = read[row].split(':')
            value = value.strip()
            ROUTES[key] = value
    except:
        print("failed to load .htaccess")

class RequestHandler(BaseHTTPRequestHandler):

    extension_map = {
        'css'  : 'text/css',
        'html' : 'text/html',
        'js'   : 'application/javascript',
        'svg'  : 'image/svg+xml',
        'png'  : 'image/png',
        'jpg'  : 'image/jpg',
        'mp3'  : 'audio/mpeg',
        'py'   : 'py'
    }

    def do_GET(self):
        if self.path in ROUTES:
            self.path = ROUTES[self.path]

        file = self.send_head()
        if file:
            self.wfile.write(file)

    def send_head(self):
        full_path = os.getcwd() + self.path

        if os.path.isfile(full_path):  #if exists
            return self.handle_file(full_path)
        else: # all the rest
            self.handle_other(full_path)

    def handle_file(self, path):
        type = self.guess_type(self.path)

        if type == "text/html":
            try:
                interpreted = Interpreter(path).content()
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', type)
                self.send_header('Cache-control', 'no-cache')
                self.send_header('Content-length', str(len(interpreted)))
                self.end_headers()
                return interpreted
            except:
                self.log_error("Inside CGI Script failed")
        try:
            with open(path, 'rb') as reader:
                content = reader.read()
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File Not Found")
            return None

        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', type)
        self.send_header('Cache-control', 'no-cache')
        self.send_header('Content-length', str(len(content)))
        self.end_headers()

        return content

    def handle_other(self, path):
        if not os.path.exists(path): #if not exists
            self.send_error(HTTPStatus.NOT_FOUND, "File Not Found")

        # if is a dir
        # if is not a dir and ends with '/'
        # error 304

    def guess_type(self, path):
        try:
            return self.extension_map[path.split(".")[1]]
        except:
            return None

    def send_error(self, code, message=None, explain=None):
        for err in ROUTES_ERRORS:
            if err in ROUTES and ROUTES_ERRORS[err] == code:
                try:
                    with open(os.getcwd() + ROUTES[err], 'r') as reader:
                        self.error_message_format = reader.read()
                except:
                    self.log_error("custom %s error page Not Found", int(code))
                
        super(RequestHandler, self).send_error(code, message, explain)


class CGIRequestHandler(RequestHandler):
    
    def do_POST(self):
        if self.is_python():
            self.run_python()
        else:
            self.send_error(
                HTTPStatus.NOT_IMPLEMENTED,
                "Can only POST to CGI Python Scripts")

    def send_head(self):
        if self.is_python():
            return self.run_python()
        else:
            return RequestHandler.send_head(self)

    def is_python(self):
        self.script_file = self.path

        if '?' in self.path: self.script_file = self.path.split('?')[0]
        if self.guess_type(self.script_file) == "py":
            return True

        del self.script_file
        return False

    def run_python(self):
        # check if exists
        if not os.path.exists(os.getcwd() + self.script_file):
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "No such CGI script (%r)" % self.script_file)
            return

        # find an explicit query string, if exists
        try:
            query = self.path.split('?')[1]
        except:
            query = ""

        # Set CGI Environment Variables
        env = os.environ

        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command
        env['SCRIPT_NAME'] = self.script_file
        env['QUERY_STRING'] = query
        env['REMOTE_ADDR'] = self.client_address[0]
        if self.headers.get('content-type') is None:
            env['CONTENT_TYPE'] = self.headers.get_content_type()
        else:
            env['CONTENT_TYPE'] = self.headers['content-type']
        referer = self.headers.get('referer')
        if referer:
            env['HTTP_REFERER'] = referer
        accept = self.headers.get_all('accept', ())
        env['HTTP_ACCEPT'] = ','.join(accept)
        ua = self.headers.get('user-agent')
        if ua:
            env['HTTP_USER_AGENT'] = ua
        length = self.headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        # send ok response
        self.send_response(HTTPStatus.OK, "Script output follows")
        self.flush_headers()

        # execute python script, pass it the os variables, and get the output
        import subprocess
        cmd = "python " + '"' + os.getcwd() + self.script_file + '"'
        try:
            nbytes = int(length)
        except (TypeError, ValueError):
            nbytes = 0
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env = env
                            )
        if self.command.lower() == "post" and nbytes > 0:
            data = self.rfile.read(nbytes)
        else:
            data = None
        stdout, stderr = p.communicate(data)
        if stderr:
            self.log_error('%s', stderr)
        else:
            self.wfile.write(stdout)
        p.stderr.close()
        p.stdout.close()
        status = p.returncode
        if status:
            self.log_error("CGI script exit status %#x", status)
        else:
            self.log_message("CGI script exited OK")


def run(server_class, handler_class, port):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    print('Started httpserver on port ', args.port)

    try:
        httpd.serve_forever()

    except KeyboardInterrupt:
        httpd.server_close()
        print("Keyboard interrupt received, exiting.")
        sys.exit(0)

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('port', type=int, default=80, 
                        help='specify alternate port (default: 80)',
                        nargs='?')

    parser.add_argument('--directory', '-d', default=os.getcwd(), 
                        help='specify alternate directory (default: current directory)')

    parser.add_argument('--cgi', action='store_true', 
                        help='run as CGI server')

    args = parser.parse_args()
    os.chdir(args.directory)

    if args.cgi:
        handler = CGIRequestHandler
    else:
        handler = RequestHandler

    create_routes()
    run(ThreadingHTTPServer, handler, args.port)
