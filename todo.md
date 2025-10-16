Pasos limpios:

- Refactorizar TelegramService y servicios externos a llamadas asíncronas o moverlas a un ThreadPoolExecutor, luego agregar una lógica de reintentos que por el momento esté obsoleta con un parámetro de reintentos o retry o request_retrys = 0. Esto principalmente para evitar que el bot se bloquee.

- Limpiar dependencias y archivos duplicados antes de seguir ampliando funcionalidad.

- Implementar el repositorio/whitelist de usuarios y agregar tests básicos; después validar manualmente el flujo con un bot de prueba.
    - Posiblemente involucre la creacion de un repository de usuarios y de chats:
       . Los chat_id son estables (grupos: enteros negativos, privados: positivos) y los user_id son permanentes para ese bot. Telegram no recicla IDs, por lo que sirven para persistencia y whitelists. (Esto a partir de la busqueda de informacion para telegram).
       . Buenas prácticas: almacenar chat_id y user_id, y considerar que los usuarios pueden cambiar username, nunca el id.
Pregunta: esta nueva estructura de repositorys involucraría generar controllers y services para trabajar con los usuarios y los repositorios?