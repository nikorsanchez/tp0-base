# Ejercicio 7

Para este ejercicio se modificó la lógica de negocio de manera que se comienza un sorteo sobre todas las apuestas enviadas por las agencias (clientes). Este sorteo comienza una vez que todas las agencias avisan al servidor (lotería nacional) que ya enviaron todas sus apuestas. Cuando el servidor realiza el sorteo, al finalizar envía los ganadores de sus respectivas agencias y por úlitmo el cliente imprime a sus ganadores, si los tiene.

## Data

Para el almacenamiento de las apuestas cuando se reciben, para cargar las apuestas una vez finalizados los envíos, y para detectar los ganadores de las apuestas, se utilizaron las funciones `store_bets`, `load_bets` y `has_won`, respectivamente, y no fueron modificadas.

## Comunicación

Se agregaron nuevas funcionalidades en ambos protocolos, por parte del cliente, ahora envía dos mensajes sin body y recibe uno con body, análogamente el servidor envía la lista de ganadores con el header correspondiente "winer_list":

```bash
HEADER_TYPE_FINISH_NOTIFY = 0x04
HEADER_TYPE_WINNERS_QUERY = 0x05
HEADER_TYPE_WINNERS_LIST  = 0x06
```

Ahora el cliente envía la notificación de que terminó de enviar todas las apuestas y además otro mensaje pidiendo los ganadores de su agencia.

Como fue mencionado el server envía los dni como cadena de bytes, y el cliente los recibe sabiendo que son fijos 8 digitos, por lo tanto luego de decodificar los bytes a string, los separa cada 8 digitos para ser procesados.

Las nuevas funciones son:
* SendFinishNotification/SendWinnersQuery
* send_winners_list/ReceiveWinnersList

## Docker compose

Para el correcto funcionamiento de comenzar la lotería se agregó a `generar-compose.sh` la variable de entorno en la configuración del server: `- EXPECTED_CLIENTS=$NUM_CLIENTS`. De esta forma el server carga en su config la variable de entorno y dependiendo de la cantidad de clientes desplegados por el yaml de cliente, va a saber cuantos clientes esperar para comenzar la lotería.

## Ejecucion

Al igual que los ejercicios anteriores, primero se debe ejecutar el generador de docker compose para crear la correcta configuración, puede elegirse 5 clientes de la siguiente forma:

`./generar-compose.sh docker-compose-dev.yaml 1` 

#### Asegurarse de ejecutar chmod +x sobre el archivo así para darle permisos de ejecución:

`sudo chmod -x generar-compose.sh docker-compose-dev.yaml` 

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