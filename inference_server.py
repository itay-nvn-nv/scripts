# curl -X POST "http://localhost:8080/" \
#      --data "word1=hello" \
#      --data "word2=hey"

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

def hello(word1, word2):
    chars1 = len(str(word1))
    chars2 = len(str(word2))
    return f"1st word '{word1}' has {chars1} characters, 2nd word '{word2}' has {chars2} characters."

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        response = "Server is running, ready to predict..."

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

        self.log_message("GET request: %s", response)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        query_params = urlparse.parse_qs(post_data)

        word1 = query_params.get('word1', [''])[0]
        word2 = query_params.get('word2', [''])[0]

        response = hello(word1, word2)

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

        self.log_message(f"POST request: {response}")

def run(server_class=HTTPServer, handler_class=MyHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting prediction server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()