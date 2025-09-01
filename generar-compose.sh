#!/bin/bash

# Check arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <output_file> <number_of_clients>"
  echo "Example: $0 docker-compose-dev.yaml 5"
  exit 1
fi

OUTPUT_FILE=$1
NUM_CLIENTS=$2

echo "Output Filename: $OUTPUT_FILE"
echo "Number of Clients: $NUM_CLIENTS"

# Check number of clients (0 to 100)
if ! [[ "$NUM_CLIENTS" =~ ^[0-9]+$ ]] || [ "$NUM_CLIENTS" -lt 0 ] || [ "$NUM_CLIENTS" -gt 100 ]; then
  echo "Error: Number of clients must be an integer between 0 and 100"
  exit 1
fi

# Generate Docker Compose file

cat > "$OUTPUT_FILE" << EOF
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - SERVER_PORT=12345
    volumes:
      - ./server/config.ini:/config.ini:ro
    networks:
      - testing_net
EOF

# Add client services if NUM_CLIENTS > 0
if [ "$NUM_CLIENTS" -gt 0 ]; then
  for i in $(seq 1 $NUM_CLIENTS); do
    cat >> "$OUTPUT_FILE" << EOF
  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
      - MAX_AMOUNT=160
    volumes:
      - ./client/config.yaml:/config.yaml:ro
      - ./.data/agency-$i.csv:/data/agency-$i.csv:ro
    networks:
      - testing_net
    depends_on:
      - server
EOF
  done
fi

# Add networks

cat >> "$OUTPUT_FILE" << EOF

networks:
  testing_net:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF

echo "Successfully generated $OUTPUT_FILE with $NUM_CLIENTS clients"