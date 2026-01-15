#!/bin/sh

cd /build
make virt_reader COM_PORT_BASE_NAME=$COM_PORT_BASE_NAME

exec ./virt_reader