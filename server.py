#!/usr/bin/env python3

import os
import json
import datetime
import hashlib
import subprocess
from flask import Flask, redirect, request, send_file, jsonify, make_response

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
def index():
    return 'OK'

with open('manifest.json', 'r') as f:
    manifest = json.load(f)
with open('digest.json', 'r') as f:
    digest = json.load(f)
with open('meta.json', 'r') as f:
    meta = json.load(f)
with open('layer.tar.gz', 'rb') as f:
    layer_data = f.read()
    layer_digest = hashlib.sha256(layer_data).hexdigest()
    layer_diffid = subprocess.check_output(['diffid/diffid', 'layer.tar.gz']).decode().strip()
    print("layer_digest:", layer_digest)
    print("layer_diffid:", layer_diffid)

meta['rootfs']['diff_ids'][0] = layer_diffid
meta_data = json.dumps(meta).encode()
meta_digest = hashlib.sha256(meta_data).hexdigest()
print("meta_digest", meta_digest)

# change digest
digest['layers'][0]['digest'] = f"sha256:{layer_digest}"
digest['layers'][0]['size'] = len(layer_data)
digest['config']['digest'] = f"sha256:{meta_digest}"
digest['config']['size'] = len(meta_data)

with open('digest.json', 'w') as f:
    json.dump(digest, f, indent=2)
digest_data = json.dumps(digest).encode()
digest_digest = hashlib.sha256(digest_data).hexdigest()
print("digest_digest:", digest_digest)

# change manifest
archs = ['amd64', 'i386']
for m in manifest['manifests']:
    ano = m['annotations']
    if m['platform']['architecture'] in archs:
        m['digest'] = f"sha256:{digest_digest}"
    if ano.get('com.docker.official-images.bashbrew.arch') in archs and ano.get('vnd.docker.reference.type') == 'attestation-manifest':
        ano['vnd.docker.reference.digest'] = f"sha256:{digest_digest}"

with open('manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
manifest_data = json.dumps(manifest).encode()
manifest_digest = hashlib.sha256(manifest_data).hexdigest()
print('manifest_digest:', manifest_digest)

def add_headers(headers, content_digest):
    headers['Date'] = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    headers['Connection'] = 'close'
    headers['docker-content-digest'] = f'sha256:{content_digest}'
    headers['docker-distribution-api-version'] = 'registry/2.0'
    headers['etag'] = f'"sha256:{content_digest}"'
    headers['strict-transport-security'] = 'max-age=10'
    headers['ratelimit-limit'] = '100;w=21600'
    headers['ratelimit-remaining'] = '99;w=21600'
    headers['docker-ratelimit-source'] = '104.28.247.69'

@app.route('/<path:path>', methods=['GET', 'HEAD', 'POST'])
def catch_all(path):
    if path.startswith('v2/library/hello-world/manifests/latest') and request.method == 'HEAD':
        response = make_response(b'', 200)
        add_headers(response.headers, manifest_digest)
        response.headers['Content-Type'] = 'application/vnd.oci.image.index.v1+json'
        response.headers['Content-Length'] = str(len(manifest_data))
        return response
    elif path.startswith(f'v2/library/hello-world/manifests/sha256:{manifest_digest}'):
        response = make_response(manifest_data)
        response.headers['Content-Type'] = 'application/vnd.oci.image.index.v1+json'
        add_headers(response.headers, manifest_digest)
        return response
    elif path.startswith(f'v2/library/hello-world/manifests/sha256:{digest_digest}'):
        response = make_response(digest_data)
        add_headers(response.headers, digest_digest)
        response.headers["Content-Type"] = "application/vnd.oci.image.manifest.v1+json"
        return response
    elif path.startswith(f'v2/library/hello-world/blobs/sha256:{layer_digest}'):
        response = make_response(layer_data)
        add_headers(response.headers, layer_digest)
        return response
    elif path.startswith(f'v2/library/hello-world/blobs/sha256:{meta_digest}'):
        response = make_response(meta_data)
        response.headers["Content-Type"] = "application/octet-stream"
        add_headers(response.headers, meta_digest)
        return response
    target_url = f"https://docker.1ms.run/{path}"
    return redirect(target_url, code=302)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
