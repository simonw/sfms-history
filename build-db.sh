#!/bin/bash

# Builds sfms.db using data from index.db - which is created using
# s3-ocr index sfms-history index.db

rm -f sfms.db

# Create tables
sqlite-utils create-table sfms.db documents \
  id text \
  title text \
  path text \
  etag text \
  --pk id

sqlite-utils create-table sfms.db pages \
  id text \
  document_id text \
  page integer \
  text text \
  --pk id

sqlite-utils add-foreign-key sfms.db \
  pages document_id documents id

# Populate documents
sqlite-utils sfms.db --attach index2 index.db "$(cat <<EOF
insert into documents select
  substr(s3_ocr_etag, 2, 8) as id,
  key as title,
  key as path,
  replace(s3_ocr_etag, '"', '') as etag
from
  index2.ocr_jobs
where
  key in (select path from index2.pages)
EOF
)"

# Populate pages
sqlite-utils sfms.db --attach index2 index.db "$(cat <<EOF
insert into pages select distinct
  substr(s3_ocr_etag, 2, 8) || '-' || page as id,
  substr(s3_ocr_etag, 2, 8) as document_id,
  page,
  text
from index2.pages
  join index2.ocr_jobs
    on index2.pages.path = index2.ocr_jobs.key;
EOF
)"

# Fix document titles
sqlite-utils convert sfms.db documents title \
  'value.split("/")[-1].split(".pdf")[0].replace("_", " ")'

# Enable full-text search
sqlite-utils enable-fts sfms.db pages text
