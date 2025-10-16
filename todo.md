TODO: 

- Implementar el repositorio/whitelist de usuario.
    - Posiblemente involucre la creacion de un repository de usuarios y de chats:
       . Los chat_id son estables (grupos: enteros negativos, privados: positivos) y los user_id son permanentes para ese bot. Telegram no recicla IDs, por lo que sirven para persistencia y whitelists. (Esto a partir de la busqueda de informacion para telegram).
       . Buenas prácticas: almacenar chat_id y user_id, y considerar que los usuarios pueden cambiar username, nunca el id.
Pregunta: esta nueva estructura de repositorys involucraría generar controllers y services para trabajar con los usuarios y los repositorios?

- Agregar una verificacion al obtener la query y el payload de la misma. Verificando si hay (latitud y longitud), y chequear con una api de maps para obtener la direccion embebida en el mensaje de telegram.

- Migrar a yaml -> luego a sqlite -> luego a sql

- Migrar a docker.