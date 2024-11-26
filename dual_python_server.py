import multiprocessing
from http.server import BaseHTTPRequestHandler, HTTPServer

class CustomHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"""
        <html>
        <head>
        <style>
            body {
                background-color: green;
                font-size: 48px;
                font-weight: bold;
            }
        </style>
        </head>
        <body>
        <p>Serving on port """ + str(self.server.server_port).encode() + b"""</p>
        </body>
        </html>
        """)

def start_server(port):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Serving on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=start_server, args=(80,))
    p2 = multiprocessing.Process(target=start_server, args=(8080,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()