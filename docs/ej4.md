# Ejercicio 4

Para este ejercicio se modificó el código de client y server, de forma que cierre correctamente y en forma debida los sockets empleados para la comunicación, si bien terminen los clientes su comunicación o si reciben la señal de `SIGTERM` dada principalmente por el comando `make docker-compose-down`, ya que internamente en el makefile se llaman las directivas:

`docker compose -f docker-compose-dev.yaml stop -t 3`
`docker compose -f docker-compose-dev.yaml down`

La directiva que contiene el "stop" es el que dispara la señal `SIGTERM`, la cual dentro de las modificaciones que se realizaron fue configurar la existencia de dicha señal y que al recibirla comience con los procesos para cerrar los sockets de la comunicación y luego terminar con el proceso completo.

Una línea importante a destacar que se añadió en la parte del `Server` que se encuentra desarrollado en lenguaje `python` es:

`self._server_socket.shutdown(socket.SHUT_RDWR)`

Ya que es importante señalizar al socket en ambas direcciones (cliente-servidor) que el socket no enviará mas información mediante dicho medio, asegurando finalizar correctamente la comunicación.

En la parte del Cliente, desarrollado en lenguaje `Go`, se agregó el uso de `chan` para comunicar entre `goroutines` para la correcta comunicación de cierre a la hora de recibir el signal de terminar el proceso y `select` utilizado para captar la señal de `SIGTERM` en ese channel.

### Prueba

Para probar dichos cambios se puede lanzar los sistemas con:
`make docker-compose-up`

Luego de esperar a que inicien los servicios, en otra consola ejecutar:

`make docker-compose-logs`

Volver a la primer consola unos segundos después, ejecutar el siguiente comando y volver a la otra consola para ver los logs:

`make docker-compose-down`

Podrá observarse como los clientes (si los hay) y el servidor terminan de forma "gracefully" sus procesos, durante la etapa de "stopping" provocada por el compose down.