# Ejercicio 3

Para el cumplimiento de la consigna, se creó un archivo `bash` ejecutable llamado `validar-echo-server.sh`, el cual permite fácilmente verificar que el server se encuentra funcionando, corriendo en el puerto especificado en la configuración (en este caso en el puerto `12345`), y que además ofrece respuesta, es decir que está libre a nuevas comunicaciones y no se encuentra bloqueado.

El ejecutable realiza operaciones en las cuales se conecta al server, mediante netcat dentro de un contenedor temporal utilizando `busybox` (suite de software open source) envía un mensaje de prueba, compara si recibe tal mensaje comparando si efectivamente realiza el `echo ...`, con varios reintentos por si el server se encuentra con poca disponibilidad o está encendiendo, e imprime:

`"action: test_echo_server | result: success"` en el caso de responder correctamente.
`"action: test_echo_server | result: fail"` en el caso de que no.

De esta forma se puede comprobar en cualquier momento (con el server previamente iniciado), que el server funciona correctamente, y sin necesidad de exponer puertos ya que se conecta directamente a la red del contenedor de docker (en este caso configurada como `NETWORK_NAME="tp0_testing_net"`).

Como lo mencionado previamente el server primero debe iniciarse, incluso si no existen clientes preparados por el generador, como por ejemplo:

`./generar-compose.sh docker-compose-dev.yaml 0`

y luego iniciar el servidor con:

`make docker-compose-up`

Aclaración, verificar que no haya quedado ningun contenedor abierto (puede verificarse con `docker ps -a`), en tal caso detenerlo y cerrar el server con:

`make docker-compose-down`

y en caso de fallar:

`docker stop server` y luego `docker remove server`.