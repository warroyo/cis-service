# TMC CIS Service

This document outlines the workaround needed to implement certain CIS controls on TMC components installed in the cluster. 


## Overview

This workaround provides implementation of different CIS controls that may be needed for TMC components. This is done through a mutating webhook. Currently the CIS controls that are handled by this are:

* CIS 5.7.3 - deployment/daemonset must have security context set unless there is an exception for that specific resource


This needs to be done through a custom mutating webhook becuase the TMC gatekeeper has an exclusion on the `vmware-system-tmc` namespace. 


## Usage

This is implemented through a supervisor service. It is done this way becuase that allows the mutatiing webhook to be added prior to the TMC agents even when TMC is creating the cluster. This is done by adding the webhook package to the `clusterboostrap`.




