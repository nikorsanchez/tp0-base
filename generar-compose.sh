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

# Check number of clients (1 to 100)
if ! [[ "$NUM_CLIENTS" =~ ^[0-9]+$ ]] || [ "$NUM_CLIENTS" -le 0 ] || [ "$NUM_CLIENTS" -gt 100 ]; then
    echo "Error: Number of clients must be a positive integer between 1 and 100"
    exit 1
fi

# Python docker compose generator script
python3 generar-compose.py "$OUTPUT_FILE" "$NUM_CLIENTS"
