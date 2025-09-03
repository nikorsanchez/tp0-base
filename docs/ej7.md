# Ejercicio 7




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