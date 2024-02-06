#!/bin/bash

# this script builds the python partner api example

mkdir -p protos
# we only copy in the most recent version of the API, not the deprecated one
cp ../../../emporia-v2/protos/partner_api2.proto ./protos/

# install grpc compiler and other dependencies

pip3 install -r requirements.txt

# compile proto file
python3 -m grpc_tools.protoc -Iprotos --python_out=. --grpc_python_out=. protos/partner_api2.proto

# to run:   python3 emporia-energy-api-client.py
