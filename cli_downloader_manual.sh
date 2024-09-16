#!/bin/bash

DIST="linux" # change to "darwin" for macos

### runai-adm CLI ###
RUNAI_CTRL_PLANE_URL="" # i.e "https://mycompany.run.ai"
wget $RUNAI_CTRL_PLANE_URL/v1/k8s/admin-cli/$DIST -O runai-adm
chmod +x runai-adm

### runai CLI ###
RUNAI_CLUSTER_URL="" # i.e "https://myrunaicluster.mycompany.net"
wget $RUNAI_CLUSTER_URL/cli/$DIST -O runai
chmod +x runai