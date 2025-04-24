#!/usr/bin/env python

from flask import Flask, request, jsonify
import json
import logging
import jsonpatch
import base64
import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
config.load_incluster_config()
api = client.CustomObjectsApi()
python_image = os.getenv('PYTHON_IMAGE', 'python:3.9')

def pkg_patch(action,index,packageVersion):
    patch = [{"op": action, "path": f"/spec/additionalPackages/{index}","value":{"refName": f"cis-webhook.field.vmware.com.{packageVersion}","valuesFrom":{"inline":{"python_image": python_image}}}}]
    return patch
@app.route('/mutate', methods=['POST'])
def webhook():
    packageVersion = os.getenv('CIS_WEBHOOK_VERSION', '1.0.0')
    
    request_json = request.get_json()
    default_response = jsonify(
            {
                "apiVersion": request_json.get("apiVersion"),
                "kind": request_json.get("kind"),
                "response": {
                    "uid": request_json["request"].get("uid"),
                    "allowed": True
                }
            }
        )
    app.logger.debug(request_json)
    if not request_json:
        return default_response
    bootstrap = request_json['request']['object']
    cluster_name = bootstrap['metadata']['name']
    namespace = bootstrap['metadata']['namespace']
    try:
        cluster_object = api.get_namespaced_custom_object(
            group="cluster.x-k8s.io",
            version="v1beta1",
            name=cluster_name,
            namespace=namespace,
            plural="clusters",
        )
    except ApiException as e:
        logging.error(f"failed to get cluster data for {cluster_name}")
        raise
    if "cis-mutate.field.vmware.com" not in cluster_object['metadata']['labels']:
        app.logger.info(f"request for {cluster_name} does not contain the cis label, skipping") 
        return default_response
    
    patch = pkg_patch("add","-",packageVersion)
    for index, package in enumerate(bootstrap['spec']['additionalPackages']):
        if "cis-webhook.field.vmware.com" in package['refName']:
            app.logger.info(f"request for {cluster_name} has cis package, patching") 
            patch = pkg_patch("replace",f"{index}",packageVersion)
    
    app.logger.debug(patch)
    json_patch = jsonpatch.JsonPatch(patch)
    base64_patch = base64.b64encode(json_patch.to_string().encode("utf-8")).decode("utf-8")
    return jsonify(
        {
            "apiVersion": request_json.get("apiVersion"),
            "kind": request_json.get("kind"),
            "response": {
                "uid": request_json["request"].get("uid"),
                "allowed": True,
                "status": {"message": "configuring cluster for cis fix webhook"},
                "patchType": "JSONPatch",
                "patch": base64_patch
            }
        }
    )

if __name__ == '__main__':
    app.logger.info("starting cis mutating webhook")
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=('/ssl/tls.crt', '/ssl/tls.key'))