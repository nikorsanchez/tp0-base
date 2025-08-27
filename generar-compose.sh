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

# Check .yaml extension
if [[ "$OUTPUT_FILE" == *.* ]]; then
    EXTENSION="${OUTPUT_FILE##*.}"
    if [[ "$EXTENSION" != "yaml" ]]; then
        echo "Error: Output file extension must be .yaml"
        exit 1
    fi
else
    OUTPUT_FILE="${OUTPUT_FILE}.yaml"
    echo "No extension detected. Output filename changed to: $OUTPUT_FILE"
fi

# Python docker compose generator script
python3 generar-compose.py "$OUTPUT_FILE" "$NUM_CLIENTS"

if [ $? -eq 0 ]; then
    echo "Docker Compose file generated successfully: $OUTPUT_FILE"
else
    echo "Error generating Docker Compose file"
    exit 1
fi
