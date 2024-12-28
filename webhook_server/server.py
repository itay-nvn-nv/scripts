from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
import ssl
import sys
import os
from urllib.parse import urlparse

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print(f"=== Received POST request on path: {self.path} ===", file=sys.stderr)

        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path != '/mutate':
            print(f"Wrong path! Expected /mutate, got {path}", file=sys.stderr)
            self.send_response(404)
            self.end_headers()
            return
            
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        try:
            admission_review = json.loads(body)
            print(f"Processing admission review: {json.dumps(admission_review, indent=2)}", file=sys.stderr)
            
            request = admission_review.get('request', {})
            if not request:
                raise ValueError("No 'request' field in admission review")
            
            # Extract namespace from request
            namespace = request.get('namespace', '')
            print(f"Request for namespace: {namespace}", file=sys.stderr)
            
            # Create the patch
            patch = [
                {
                    "op": "add",
                    "path": "/spec/containers/-",
                    "value": {
                        "name": "lolz",
                        "image": "nginx",
                        "command": ["sleep"],
                        "args": ["infinity"]
                    }
                }
            ]
            
            response = {
                "apiVersion": "admission.k8s.io/v1",
                "kind": "AdmissionReview",
                "response": {
                    "uid": request.get('uid'),
                    "allowed": True,
                    "patchType": "JSONPatch",
                    "patch": base64.b64encode(json.dumps(patch).encode()).decode()
                }
            }
            
            print(f"Sending response: {json.dumps(response, indent=2)}", file=sys.stderr)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"Error processing request: {str(e)}", file=sys.stderr)
            self.send_error(500)

if __name__ == "__main__":
    print("Starting webhook server on port 8443...", file=sys.stderr)
    print("Waiting for admission review requests...", file=sys.stderr)
    
    server_address = ('0.0.0.0', 8443)
    httpd = HTTPServer(server_address, WebhookHandler)

    # Load certificate and key
    ssl_cert = '/app/certs/webhook.crt'
    ssl_key = '/app/certs/webhook.key'

    if not os.path.exists(ssl_cert) or not os.path.exists(ssl_key):
        print("TLS certificate and/or key not found. Serving without TLS.", file=sys.stderr)
    else:
        httpd.socket = ssl.wrap_socket(httpd.socket, 
                                        certfile=ssl_cert, 
                                        keyfile=ssl_key, 
                                        server_side=True)
    

    httpd.serve_forever()