#!/bin/bash
# Usage: ./validar-echo-server.sh
SERVER_NAME="server"
SERVER_PORT=12345
NETWORK_NAME="tp0_testing_net"
SUCCESS_MSG="action: test_echo_server | result: success"
FAILURE_MSG="action: test_echo_server | result: fail"
MAX_RETRIES=5
RETRY_INTERVAL=1
TEST_MSG="Testing server connection"

for i in $(seq 1 $MAX_RETRIES); do
   RESPONSE=$(docker run --network "$NETWORK_NAME" --rm busybox:latest sh -c "echo '$TEST_MSG' | nc -w 2 $SERVER_NAME $SERVER_PORT")

    if [ "$RESPONSE" == "$TEST_MSG" ]; then
        echo "$SUCCESS_MSG"
        EXIT_CODE=0
    fi

    sleep $RETRY_INTERVAL

done

echo "$FAILURE_MSG"
exit 1
