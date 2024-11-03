from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

# Define the hello function
def hello(input_text):
    text = str(input_text)
    chars = len(text)
    return f"String '{text}' has {chars} characters"

# Define request handler
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        parsed_path = urlparse.urlparse(self.path)
        query_params = urlparse.parse_qs(parsed_path.query)
        input_text = query_params.get('input_text', [''])[0]

        # Call the hello function
        response = hello(input_text)

        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

# Set up the server
def run(server_class=HTTPServer, handler_class=MyHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting http server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
