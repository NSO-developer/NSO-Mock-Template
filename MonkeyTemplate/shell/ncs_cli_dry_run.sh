#!/bin/bash

ncs_cli -C -u admin >> /tmp/template_data.txt << EOF
config
template apply-config-template name $1
commit dry-run outformat native
exit
EOF
