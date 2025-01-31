from flask import Flask, request, jsonify

app = Flask(__name__)

ssl_cert = '/app/certs/webhook.crt'
ssl_key = '/app/certs/webhook.key'

@app.route('/validate', methods=['POST'])
def validate_pvc():
    review = request.json
    request_uid = review['request']['uid']
    pvc_spec = review['request']['object']['spec']

    # Extract requested storage size
    storage = pvc_spec.get('resources', {}).get('requests', {}).get('storage', '0Gi')
    requested_size_gb = int(storage.rstrip('Gi'))  # Convert "20Gi" to 20

    # Validation logic
    if requested_size_gb > 20:
      response = {
          "apiVersion": "admission.k8s.io/v1",
          "kind": "AdmissionReview",
          "response": {
              "uid": request_uid,
              "allowed": False,
              "status": {
                  "message": "PVC size exceeds the 20 GB limit."
              }
          }
      }
      return jsonify(response)

    # Allow if size is within limit
    response = {
      "apiVersion": "admission.k8s.io/v1",
      "kind": "AdmissionReview",
      "response": {
        "uid": request_uid,
        "allowed": True
        }
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443, ssl_context=(ssl_cert, ssl_key), debug=True)