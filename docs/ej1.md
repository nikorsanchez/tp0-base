# Ejercicio 1

En este ejercicio se creó un archivo `bash` ejecutable llamado `generar-docker.sh`, el cual facilita la configuración del docker compose, permitiendo a través de su ejecución un autocompletado del documento necesario para iniciar el programa, evitando cambiar configuraciones extras, simplemente ejecutandolo con la siguiente directiva:

`./generar-docker.sh <output_file> <number_of_clients>`

Como por ejemplo:

`./generar-compose.sh docker-compose-dev.yaml 5`

En este último caso creará el yaml de configuración de docker compose para 5 clientes que se conectarán al server.

Finalmente puede ejecutarse el programa mediante el comando:

`make docker-compose-up`
