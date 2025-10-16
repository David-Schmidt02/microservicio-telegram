# Ejemplos de mensajes de la API de Telegram

Telegram devuelve una estructura al realizar un get_updates con los mensajes nuevo detectados en el pool.

## Mensaje de texto

{
    "update_id": 625240589,
    "message": {
        "message_id": 21,
        "from": {
        "id": 123456789,              // ID único del usuario
        "is_bot": false,
        "first_name": "David",
        "last_name": "Pérez",
        "username": "davidp",          // @davidp
        "language_code": "es"
        },
        "chat": {
        "id": -4871163359,            // ID del grupo (negativo para grupos)
        "title": "Mi Grupo",
        "type": "supergroup"           // "private", "group", "supergroup", "channel"
        },
        "date": 1760540547,             // Timestamp Unix
        "text": "Hola bot"              // El texto del mensaje
    }
}

## Mensaje de Audio

{
    "update_id": 625240590,
    "message": {
        "message_id": 22,
        "from": {               -----> Identifica al user
        "id": 123456789,
        "first_name": "David",
        "username": "davidp"
        },                      
        "chat": {
        "id": -4871163359,
        "type": "supergroup"
        },
        "date": 1760540600,
        "voice": {                      // o "audio" para archivos de audio <- CON ESTE DETECTAMOS EL TIPO DE MENSAJE.
        "duration": 3,
        "mime_type": "audio/ogg",
        "file_id": "AwACAgEAAxk...",  // ID para descargar el archivo
        "file_unique_id": "AgADzQUA",
        "file_size": 12345
        }
    }
}