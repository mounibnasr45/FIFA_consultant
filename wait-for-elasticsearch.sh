#!/bin/bash

# Wait for Elasticsearch to be ready
echo "Waiting for Elasticsearch..."
until curl -s http://elasticsearch:9200 >/dev/null; do
    sleep 1
done

echo "Elasticsearch is up - executing command"

# Create index with mapping
curl -X PUT "http://elasticsearch:9200/fifa_laws" -H 'Content-Type: application/json' -d @fifa_laws_mapping.json

# Index the documents
curl -X POST "http://elasticsearch:9200/fifa_laws/_bulk" -H 'Content-Type: application/json' --data-binary @fifa_laws_data.json

echo "Initialization complete"import streamlit as st