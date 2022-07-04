#!/bin/bash
SFMS_PASSWORD_HASH='pbkdf2_sha256$260000$0427d3f9bd2936ca4e7243321242c674$OjCOtKOVa9UPYq0DsUjCastYHrQQlpFdh/0GZfbVteU=' \
  datasette . -p 8006 --reload
