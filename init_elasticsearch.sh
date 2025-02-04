#!/bin/bash

set -e

# Wait for Elasticsearch to start
until curl -s http://elasticsearch:9200; do
  echo "Waiting for Elasticsearch..."
  sleep 1
done

# Check if the index already exists
if curl -s -o /dev/null -w "%{http_code}" http://elasticsearch:9200/fifa_laws | grep -q "200"; then
  echo "Index fifa_laws already exists. Skipping index creation."
else
  # Create the index and mapping
  curl -X PUT "http://elasticsearch:9200/fifa_laws" -H 'Content-Type: application/json' -d @fifa_laws_mapping.json
fi

# Index the data
if ! curl -X POST "http://elasticsearch:9200/fifa_laws/_bulk" -H 'Content-Type: application/json' --data-binary @fifa_laws_data.json; then
  echo "Error: Bulk request failed. Ensure that the data file is correctly formatted."
  exit 1
fi

echo "Elasticsearch setup complete!"