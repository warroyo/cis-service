# TMC CIS Service

This document outlines the workaround needed to implement certain CIS controls on TMC components installed in the cluster. 


## Overview

This workaround provides implementation of different CIS controls that may be needed for TMC components. This is done through a mutating webhook. Currently the CIS controls that are handled by this are:

* CIS 5.7.3 - deployment/daemonset must have security context set unless there is an exception for that specific resource

The agents deployed into the `vmware-system-tmc` namespace need remediation for this control. This needs to be done through a custom mutating webhook becuase the TMC gatekeeper has an exclusion on the `vmware-system-tmc` namespace. This also needs to be implemented prior to TMC being installed so that the webhook can take affect. using a custom mutating webhook that is deployed through a VKS supervisor service handles this. 


## How it works

There are two mutating webhooks in play:
1. The cis-service, this is deployed as a supervisor service. The supervisor service installs the mutating webhook and controller along with the package for the second mutating webhook(cis-webhook) that will be deployed into workload clusters. The cis-service webhook watches for clusters to be created that have the cis label(`cis-mutate.field.vmware.com`), specifically `clusterbootstraps` and modifies them to include an additional package. This additional package is the cis-webhook. teh clusterboostrap will handle pushing the package to the cluster and creating the package install.
2. the cis-webhook, this is installed through the previous webhook. This handles implementing the cis controls on the TMC agents. This is done by watching for any deployments or daemonsets in the `vmware-system-tmc` namespace and injecting the `securityContext` that is needed

## Install

1. login into VCenter and go to the worload management->services page
2. add a new service and upload the `cis-service.yml`
3. add any additional values that are needed, most commonly used will be the `python_image` which overrides the image location for the webhooks. 
4. install


## Validation

There should now be a pod running in the supervisor cluster 

```bash
k get pods -n svc-cis-service-domain-c27
```

There should also be 2 new packages installed

```bash
k get pkg -A | grep -i cis
```

## Validate a workload cluster

1. create a new workload cluster using tmc and add the label `cis-mutate.field.vmware.com: true` to the cluster
2. check that the  `clusterbootstrap` is updated in the supervisor. you should see that there is an additional package added for the cis-webhook.

```bash
k get clusterbootstrap -n <provisioner> <clustername> -o yaml
```
3. login to the cluster after it is created and check that the webhook is running
```bash
k get pkgi -A | grep cis # this should show the pkgi reconciled

k get pods -n cis-service
```

4. Check to see if the TMC pods have the securityContext set

```bash
k get pods -n vmware-system-tmc -o yaml | grep -i securitycontext -C 10
```

# Development

## Build/Release

1. set the version

```bash
export VERSION=1.0.0
make release
```





