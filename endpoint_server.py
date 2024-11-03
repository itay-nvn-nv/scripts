from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

# Define the hello function to handle multiple inputs
def hello(word1, word2):
    chars1 = len(word1)
    chars2 = len(word2)
    return f"1st word: '{word1}' ({chars1} characters). 2nd word: '{word2}' ({chars2} characters)."

# Define request handler
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Respond with a fixed message for every GET request
        response = "Server is running, ready to predict..."

        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def do_POST(self):
        # Get content length for reading the body of POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        query_params = urlparse.parse_qs(post_data)

        # Parse data for POST requests
        word1 = query_params.get('word1', [''])[0]
        word2 = query_params.get('word2', [''])[0]

        # Call the hello function with multiple inputs
        response = hello(word1, word2)

        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

# Set up the server
def run(server_class=HTTPServer, handler_class=MyHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting prediction server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

# curl -X POST "http://localhost:8080/" \
#      --data "word1=hello" \
#      --data "word2=hey"
