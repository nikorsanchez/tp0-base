#!/bin/bash
# Usage: ./validar-echo-server.sh
SERVER_NAME="server"
SERVER_PORT=12345
NETWORK_NAME="tp0_testing_net"
SUCCESS_MSG="action: test_echo_server | result: success"
FAILURE_MSG="action: test_echo_server | result: fail"
TEST_MSG="Testing server connection"

RESPONSE=$(docker run --network "$NETWORK_NAME" --rm busybox:latest sh -c "echo '$TEST_MSG' | nc $SERVER_NAME $SERVER_PORT")

if [ "$RESPONSE" == "$TEST_MSG" ]; then
   echo "$SUCCESS_MSG"
   EXIT_CODE=0
else
   echo "$FAILURE_MSG"
   EXIT_CODE=1
fi

exit $EXIT_CODE
