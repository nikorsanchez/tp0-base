# Ejercicio 8

Para este ejercicio, se implementó que el servidor puede recibir conexiones de los clientes, recibir mensajes y procesarlos simultáneamente, utilizando la librería `multiprocessing`, de esta manera paralelizando las acciones del servidor.

## Concurrencia

Utilizando la librería `multiprocessing` de pythoh, para poder manejar conexiones entrantes de los clientes y el procesamiento de los datos enviados concurrentemente. El servidor crea un proceso independiente hijo por cada cliente que se conecta permitiendo que cada proceso hijo se encargue de su cliente. 

Se utiliza como mecanismo de sincronización para acceso a los datos un lock (utilizaod en el código en `server.py` como `self.manager.Lock()`), para evitar race conditions en la escritura cuando se utiliza la función `store_bets()`, protegiendo la sección crítica cuando varios procesos quieran escribir sus apuestas.

```sh
with bets_lock:  # Toma el lock
    store_bets(bet_objects) # Realiza la operación crítica
```

Para la sincronización de los procesos hijos al momento de empezar a realizar la búsqueda del ganador de las apuestas, se utilzó la condition variable `Condition` como `manager.Condition()`, de esta forma los procesos hijos que ya hayan recibido el mensaje de parte del cliente que terminaron de enviar apuestas, quedan a la espera que todos los procesos hijos procesando aún los datos finalicen, utilizando `condition.wait()`, y cuando el útlimo finalice avisará a todos con `condition.notify_all()`.

```sh
with condition:  # Toma el acceso a la condition
    finished_clients.value += 1  # Modificación segura
    
    if finished_clients.value == expected_clients:
        condition.notify_all()  # Notifica a todos los procesos
    else:
        condition.wait()  # Libera temporalmente el Condition y espera
```

Para el caso de lectura con `load_bets()` no es necesario un lock ya que dada la lógica de negocio, no se modifica más el archivo de apuestas ya que comienzan a leer los procesos únicamente cuando se terminaron de agendar apuestas.

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