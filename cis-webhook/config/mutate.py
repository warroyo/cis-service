#!/usr/bin/env python

from flask import Flask, request, jsonify
import json
import logging
import jsonpatch
import base64

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

deployments = []

podSecuritySpec = {"fsGroup":1000,"fsGroupChangePolicy":"Always","supplementalGroups":[1000],"sysctls":[{"name":"net.ipv4.ping_group_range","value":"0 2147483647"}]}
containerSecuritySpec = {"runAsNonRoot":True,"runAsGroup":1000,"capabilities":{"drop":["NET_RAW"]},"seLinuxOptions":{"type":"default"},"seccompProfile":{"type":"RuntimeDefault"},"allowPrivilegeEscalation":False,"privileged":False,"readOnlyRootFilesystem":True}

def podTemplatePatch(op, path):
    patch = {"op": op, "path": f"{path}","value": podSecuritySpec}
    return patch

def containerPatch(op,path):
    patch = {"op": op, "path": f"{path}","value":containerSecuritySpec}
    return patch

def patch(name,spec,path):
    patches = []
    if "securityContext" in spec:
        if spec['securityContext'] == podSecuritySpec:
            app.logger.info(f"security context already set on {name} pod spec")
        else:
            patch = podTemplatePatch("replace",f"{path}/securityContext")
            patches.append(patch)
            app.logger.info(f"security context already set on {name} pod spec but doesn't match, replacing")
    else:
        patch = podTemplatePatch("add", f"{path}/securityContext")
        patches.append(patch)
        app.logger.info(f"security context not set on {name}, adding")
    
    if "securityContext" in spec['containers'][0]:
        if spec['containers'][0]['securityContext'] == containerSecuritySpec:
            app.logger.info(f"security context already set on {name} container spec")
        else:
            patch = containerPatch("replace",f"{path}/containers/0/securityContext")
            patches.append(patch)
            app.logger.info(f"security context already set on {name} container spec but doesn't match, replacing")
    else:
        patch = containerPatch("add",f"{path}/containers/0/securityContext")
        patches.append(patch)
        app.logger.info(f"security context not set on {name} container, adding")
    return patches

@app.route('/mutate', methods=['POST'])
def webhook():
    patches = []
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
    if request_json['request']['object']['kind'] == "Deployment":
        deployment = request_json['request']['object']
        deployment_name = deployment['metadata']['name']
        patches = patch(deployment_name,deployment['spec']['template']['spec'],"/spec/template/spec")

    elif request_json['request']['object']['kind'] == "CronJob":
        cj = request_json['request']['object']
        cj_name = cj['metadata']['name']
        patches = patch(cj_name,cj['spec']['jobTemplate']['spec']['template']['spec'],"/spec/jobTemplate/spec/template/spec")
        
   
    app.logger.debug(patches)
    json_patch = jsonpatch.JsonPatch(patches)
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