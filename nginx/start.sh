#!/bin/bash
service nginx start
consul-template -consul=$CONSUL_URL -template="/templates/default.ctmpl:/etc/nging/conf.d/default.conf:service nginx reload"
