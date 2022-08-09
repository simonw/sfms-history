#!/bin/bash
SFMS_PASSWORD_HASH='pbkdf2_sha256$260000$0427d3f9bd2936ca4e7243321242c674$OjCOtKOVa9UPYq0DsUjCastYHrQQlpFdh/0GZfbVteU=' \
  datasette sfms.db \
    -p 8006 \
    --reload \
    --plugins-dir plugins \
    --template-dir templates \
    --static static:static \
    -m metadata.yml
