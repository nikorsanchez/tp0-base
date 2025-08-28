#!/bin/bash
# Usage: ./validar-echo-server.sh
SERVER_NAME="server"
SERVER_PORT=12345
NETWORK_NAME="tp0_testing_net"
TEST_MSG="Testing server connection"
RESPONSE=$(docker run --rm --network "$NETWORK_NAME" busybox sh -c "echo '$TEST_MSG' | nc $SERVER_NAME $SERVER_PORT")

if [ "$RESPONSE" == "$TEST_MSG" ]; then
   echo "action: test_echo_server | result: success"
   EXIT_CODE=0
else
   echo "action: test_echo_server | result: fail"
   EXIT_CODE=1
fi

exit $EXIT_CODE
