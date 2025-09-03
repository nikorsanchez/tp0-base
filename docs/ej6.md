# Ejercicio 6

Para este inciso, se agregó la funcionalidad de que se pueda aprovechar un mismo mensaje para enviar múltiples apuestas, por lo tanto el cliente lee de un archivo múltiples apuestas, las envía y se reciben en el servidor y procesan todas juntas, con el fin de optimizar el flujo del canal de comunicación.

## Dataset

Para eso se modificó inicialmente el `generar-compose.sh` para poder generar automáticamente la configuración del docker, de manera que se inyecten los archivos a leer respectivamente a cada cliente, por enunciado hasta 5 clientes que son los 5 archivos presentes en el zip dentro de la carpeta en root `./data/dataset.zip`, mediante la configuración:

```bash
volumes:
      - ...
      - ./.data/agency-$i.csv:/data/agency-$i.csv:ro
```

## Comunicación por Chunks/Batchs

Se agregó a la lógica de negocio la característica de poder enviar en un solo mensaje una cierta cantidad de apuestas del cliente al servidor, con el mismo sistema del anterior ejercicio de serialización, deserialización de mensajes, manteniendo el delimitador de campos de los datos de las apuestas `|`, pero ahora agregando en el protocolo una separación entre apuestas `;`, permitiendo concatenar todas las apuestas que entren en un batch, en un solo mensaje en el cliente y luego aplicando su correcta lectura en el servidor. En el servidor se hará un conteo de todas las apuestas recibidas, pero con la salvedad de que si existe al menos un error con una apuesta, se le avisará al cliente que las envió que hubo un error en el guardado de apuestas.

Al recibir un error, el cliente dejará de enviar información si algun le resta enviar, y finalizará el sistema. De caso contrario, seguirá enviando batches de apuestas hasta terminar de leer todo el archivo.

En caso de un almacenamiento de apuestas correcto el server imprimirá un formato:

- `action: apuesta_almacenada | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`

De lo contrario si alguna falla:

- `action: apuesta_almacenada | result: fail | error: ${ERROR}`

Y se responderá al cliente respectivamente:

- `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`

- `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`

## Lectura de archivos

Para que los clientes puedan leer los archivos correspondientes se creó un módulo de `utils`, donde se abre el archivo `.csv`, se lee linea por linea con un `scanner`, y se parsean de los textos de los archivos la estructura `Bet` definida previamente. De esta forma el cliente ya tiene una lista de Bets lista para enviar. Según el enunciado cada mensaje no debe superar los 8kB, por lo que se decidió arbitrariamente una cantidad máxima de 160 archivos de lectura por batch, teniendo un valor cercano, dejando un margen en caso de cambiar el archivo del dataset. Puede modificarse la configuración en el generador en la parte:

```bash
environment:
      - ...
      - MAX_AMOUNT=160
```

Queda a modo de aclaración que en la descripción de este documento en el inciso de [Dataset](#dataset), los archivos a leer se configuran y se inyectan con el path `/data/agency-{N}.csv` y no `/.data/...` como lo está en la arquitectura de carpetas del proyecto.

## Ejecucion

Al igual que los ejercicios anteriores, primero se debe ejecutar el generador de docker compose para crear la correcta configuración, puede elegirse 5 clientes de la siguiente forma:

`./generar-compose.sh docker-compose-dev.yaml 1` 

#### Asegurarse de ejecutar chmod +x sobre el archivo así para darle permisos de ejecución:

`sudo chmod -x generar-compose.sh docker-compose-dev.yaml 1` 

Para poder funcionar es necesario descomprimir primero el dataset para obtener los 5 archivos `.csv` que contiene el proyecto. En caso de ya tener algunos archivos o haber ejecutado los tests, tomar la precaución de borrar y volver a descomprimir el archivo `.zip`.

Para borrar y limpiar los `.csv`, ejecutar en la terminal dentro de la raíz del proyecto:

`rm .data/*.csv`

Luego si es la primera vez o ya se ha eliminado los datos remanentes, abrir una nueva consola ubicarse en la raíz del proyecto, trasladarse a la dirección `.data/` y descomprimir de la siguiente manera:

```bash
cd .data/
unzip dataset.zip
cd ..
```

Una vez generada la configuracion del docker compose, ejecutar el inicio y luego en otra consola los siguientes comandos:

```bash
make docker-compose-up
make docker-compose-logs
```

Una vez finalizado puede limpiarse los contenedores con:

`make docker-compose-down`