# Ejercicio 2

En este ejercicio se ha modificado el generador de docker compose `generar-compose.sh` de manera que se cree un volumen para cada cliente y para el servidor dentro del docker-compose.yaml.

Se agregó en el generador:

Para el server:
`./server/config.ini:/config.ini:ro`

Para el cliente:
`./client/config.yaml:/config.yaml:ro`

Estos volúmenes agregados hacen que se pueda acceder a los contenedores de los archivos configurados sin tener que reconstruir la imagen cada vez que la configuración es modificada.
Las lineas agregadas implican que esos archivos de configuración de cada servicio se montan en su contendedor con la ruta especificada, y se agrega la linea `ro` (read only) para que el contenedor no pueda modificarlo.

De esta manera, cualquier modificación realizada en los archivos de configuración impactarán sus cambios automaticamente cuando se lancen los contenedores.

También se eliminó del generador las lineas `LOGGING_LEVEL=DEBUG` tanto en el servidor como en los clientes ya que forzaba que el sistema de logs sea del tipo DEBUG y eso sobreescribía las configuraciones de cada Dockerfile de los servicios.