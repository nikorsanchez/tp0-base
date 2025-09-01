# Ejercicio 5

En este ejercicio, se implementó una nueva lógica de negocio reutilizando cierta parte del código previo a los otros ejercicios. Como fue especificado en la consigna, ahora se trata de una comunicación entre cliente, que pasará a ser una agencia de quiniela, el cual envía una apuesta realizada por una persona a una central de lotería nacional, la cual ahora pasaría a ser el servidor. El servidor procesa el mensaje de la apuesta y le envía si fue procesada correctamente o no.

## Comunicación

Para esta comunicación, se realizó un sistema de protocolos tanto del lado del servidor como del cliente, mediante el diseño de una estructura de mensajes compuestos de la siguiente manera:

| Campo   | Tamaño                | Descripción                                 |
|---------|-----------------------|---------------------------------------------|
| HEADER  | 1 byte                | Tipo de mensaje                             |
| LENGTH  | 2 bytes               | Longitud del cuerpo del mensaje             |
| BODY    | N bytes (variable)    | Mensaje serializado                         |


El Header consta de 1 byte con dos tipos de mensaje: con valor	0x01 = Apuesta, 0x02 = Confirmación, para poder detectar que tipo de mensaje se recibe o envía.

Se optó por 2 bytes de longitud como para dejar un margen mayor por si el nombre o apellido llegara a ser muy largo, pero el espacio es más que suficiente de esta manera.

Luego la información es enviada en el mensaje, con serialización y deserializacion en su recepción y envío. También está contemplado las transformaciones de little endian a big endian, para evitar posibles errores en la transmisión. Se separa con un caracter delimitador, los distintos campos de los datos del mensaje en un orden determinado, para luego ser deserializado y leido correctamente en su recepción para poder saber los límites de bytes enviados por cada campo ya que el nombre y apellido tienen mayor margen de variacion.

En el caso del mensaje de confirmación de que si la apuesta fue recibida y almacenada correctamente, se responde solo con un header con tal tipo de confirmación si fue efectiva o un header de que ha fallado, sin ningún dato adicional, para hacer mas óptima la comunicación.

A su vez, se manejó correctamente los casos de los fenómenos `short read` y `short write`, implementando en los respectivos lenguajes con funciones donde por ejemplo se utilizan `ReadFull` para garantizar leer todos los bytes recibidos, y en el caso para escribir los bytes se implementó una funcion `writeFull` donde un loop se asegura que se escriban todos los bytes hasta completar los datos a enviar.

## Configuración

En la consigna es pedido que se configure el cliente para ejecutarse con los datos necesarios de las apuestas realizadas en él, mediante variables de entorno, por lo tanto para el correcto funcionamiento y por como se viene ejecutando los sistemas cliente-servidor, se agregó al `generar-compose.sh` como variables de entorno, las cuales luegos son llamadas en la creación de la apuesta.

## Ejecución

Al igual que los otros ejercicios anteriores, simplemente se puede generar el compose, ahora con las nuevas variables de entorno:


`./generar-compose.sh docker-compose-dev.yaml 1`

Luego iniciar los servicios con:

`make docker-compose-up`

Aclaración, verificar que no haya quedado ningun contenedor abierto al finalizar (puede verificarse con `docker ps -a`), en tal caso detenerlo y cerrar el server con:

`make docker-compose-down`

En caso de fallar:

```bash
docker stop server
docker remove server
```

Puede verificarse el correcto funcionamiento a partir del sistema de logs una vez que el sistema haya iniciado utilizando en la consola u otra consola el siguiente comando:

`make docker-compose-logs`


