# Microservicio de Telegram - Procesador de Audio y Texto

Microservicio en Python que procesa mensajes de audio y texto en grupos de Telegram. Los audios se transcriben usando una API externa y tanto las transcripciones como los mensajes de texto se envían a un sistema de queries para obtener respuestas inteligentes.

## Características

- Bot de Telegram con polling cada 2-3 segundos (configurable)
- Detección automática de mensajes de audio/voz y texto
- Transcripción de audio mediante API externa
- Procesamiento asíncrono con asyncio
- Manejo de sesiones por grupo de Telegram
- Validación de datos con Pydantic
- Logging detallado con niveles configurables
- Limpieza automática de archivos temporales

---

## Instalación

### 1. Clonar e instalar dependencias

```bash
git clone <url-del-repositorio>
cd microservicio-telegram

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia `.env.example` a `.env` y configura:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
TRANSCRIPTION_API_URL=https://tu-api.com/transcribe
QUERY_SYSTEM_URL=https://tu-sistema.com/query
POLLING_INTERVAL=2.5
LOG_LEVEL=INFO
```

### 3. Configurar el Bot de Telegram

1. Busca **@BotFather** en Telegram y envía `/newbot`
2. Guarda el token en `TELEGRAM_BOT_TOKEN`
3. Agrega el bot a tu grupo
4. Obtén el Chat ID visitando: `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Copia el `chat.id` en `TELEGRAM_CHAT_ID`
6. **Importante:** Desactiva Privacy Mode enviando `/setprivacy` a @BotFather

### 4. Ejecutar

```bash
python main.py
```

---

## Estructura del Proyecto

```
microservicio-telegram/
├── src/
│   ├── bot.py                      # Orquestador principal (TelegramAudioBot)
│   ├── schemas.py                  # Modelos Pydantic para validación
│   ├── config/
│   │   └── settings.py             # Configuración centralizada
│   ├── services/
│   │   ├── telegram_service.py     # Cliente de Telegram API
│   │   ├── transcription_service.py # Servicio de transcripción
│   │   ├── query_service.py        # Servicio de queries
│   │   └── user_service.py         # Gestión de usuarios
│   └── utils/
│       └── logger.py               # Configuración de logging
├── temp_audio/                     # Archivos temporales (auto-creado)
├── main.py                         # Punto de entrada
└── requirements.txt
```

---

## Arquitectura

### Patrón de Capas

```
main.py
    ↓
TelegramAudioBot (Orquestador)
    ↓
┌─────────────┬─────────────┬─────────────┐
│  Telegram   │Transcription│   Query     │
│  Service    │  Service    │  Service    │
└─────────────┴─────────────┴─────────────┘
```

### Patrón Callback

El proyecto usa **callbacks** para mantener bajo acoplamiento:

```python
await telegram_service.start_polling(
    audio_callback=bot.process_audio_message,  # Se ejecuta al detectar audio
    text_callback=bot.process_text_message     # Se ejecuta al detectar texto
)
```

**Ventajas:**
- Bajo acoplamiento (Service no depende del Bot)
- Alta testabilidad
- Servicios reutilizables

---

## Flujo Detallado del Sistema

### 1. Inicio del Servicio

```
python main.py
    ↓
TelegramAudioBot.__init__()
    ↓ Inicializa 3 servicios:
    - TelegramService (maneja Telegram)
    - TranscriptionService (transcribe audios)
    - QueryService (envía a sistema externo)
    ↓
bot.start() → asyncio.run()
```

### 2. Validación y Configuración

```
settings.validate()
    ↓ Verifica que existan:
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_CHAT_ID
    - TRANSCRIPTION_API_URL
    - QUERY_SYSTEM_URL
    ↓
Si falta alguna, lanza ValueError y detiene el programa
```

### 3. Ciclo de Polling

```
Cada 2.5 segundos (configurable):
    ↓
get_updates(offset=last_update_id + 1)
    ↓
Recibe lista de updates (mensajes nuevos)
    ↓
Procesa cada mensaje en orden cronológico:
    ├── ¿Tiene "voice" o "audio"? → Procesa como audio
    └── ¿Tiene "text"? → Procesa como texto

(Mantiene el orden cronológico de los mensajes)
```

### 4A. Flujo de Mensajes de AUDIO

```
Usuario envía audio en Telegram
    ↓
TelegramService detecta mensaje con "voice" o "audio"
    ↓
Crea objeto TelegramAudioMessage (Pydantic)
    ↓
【PASO 1: DESCARGA】
download_audio(file_id)
    ↓ GET /bot{TOKEN}/getFile
    ↓ GET archivo desde Telegram
    ↓ Guarda en: temp_audio/{file_id}.ogg
    ↓
【PASO 2: TRANSCRIPCIÓN】
transcription_service.transcribe_audio(file_path)
    ↓ POST {TRANSCRIPTION_API_URL}
    ↓ Respuesta: {"text": "texto transcrito"}
    ↓
【PASO 3: QUERY AL SISTEMA】
session_id = f"telegram-group-{chat_id}"
    ↓
query_service.send_query(transcription, session_id)
    ↓ POST {QUERY_SYSTEM_URL}
    ↓ Body: {"question": "...", "session_id": "..."}
    ↓ Respuesta: {"success": true, "answer": "..."}
    ↓
【PASO 4: RESPUESTA EN TELEGRAM】
telegram_service.send_message()
    ↓ POST /bot{TOKEN}/sendMessage
    ↓ "🎤 Audio: {transcription}\n\n💬 Respuesta: {answer}"
    ↓
【PASO 5: LIMPIEZA】
cleanup_audio_file(temp_audio/{file_id}.ogg)
```

### 4B. Flujo de Mensajes de TEXTO

```
Usuario envía texto en Telegram
    ↓
TelegramService detecta mensaje con "text"
    ↓
Crea objeto TelegramTextMessage (Pydantic)
    ↓
【SALTA TRANSCRIPCIÓN - VA DIRECTO A QUERY】
session_id = f"telegram-group-{chat_id}"
    ↓
query_service.send_query(text, session_id)
    ↓ POST {QUERY_SYSTEM_URL}
    ↓ Body: {"question": "...", "session_id": "..."}
    ↓
【RESPUESTA EN TELEGRAM】
telegram_service.send_message()
    ↓ Responde directamente con el answer
```

### 5. Gestión de Errores

```
En cada paso, si hay error:
    ↓ logger.error(f"Descripción: {e}")
    ↓ send_message("❌ Error: {descripción}")
    ↓ cleanup (si hay archivos temporales)
    ↓ continue (no detiene el bot)
```

---

## APIs Externas

### API de Transcripción

**Request:**
```http
POST {TRANSCRIPTION_API_URL}
Content-Type: multipart/form-data

audio: <archivo.ogg>
```

**Response esperada:**
```json
{
  "text": "Texto transcrito del audio"
}
```

### API de Queries

**Request:**
```http
POST {QUERY_SYSTEM_URL}
Content-Type: application/json

{
  "question": "Texto de la pregunta o transcripción",
  "session_id": "telegram-group-123456789"
}
```

**Response esperada:**
```json
{
  "success": true,
  "answer": "Respuesta del sistema"
}
```

---

## Aspectos Técnicos Importantes

### Session Management
- Cada grupo de Telegram tiene su propio `session_id`: `telegram-group-{chat_id}`
- Permite mantener contexto de conversación en el sistema de queries
- Múltiples usuarios en el mismo grupo comparten la misma sesión

### Archivos Temporales
- Ubicación: `temp_audio/`
- Nombre: `{file_id}.ogg`
- Se eliminan inmediatamente después de procesar (éxito o error)
- El directorio se crea automáticamente si no existe

### Polling Strategy
- Usa `offset = last_update_id + 1` para evitar procesar el mismo mensaje dos veces
- **Procesamiento en orden cronológico:** Los mensajes se procesan en el mismo orden que llegan de Telegram
- Procesamiento secuencial (un mensaje a la vez) para mantener el contexto
- Intervalo configurable vía `POLLING_INTERVAL` (default: 2.5s)

### Datos del Usuario
- **Extraídos:** `user_id`, `username`, `first_name`, `last_name`
- **Enviados al sistema:** Solo el `chat_id` (dentro del `session_id`)
- **Usados para logs:** `user.get_display_name()`

```

---

## Troubleshooting

### El bot no recibe mensajes
1. Verifica el token: `curl https://api.telegram.org/bot<TOKEN>/getMe`
2. Desactiva Privacy Mode en @BotFather
3. Confirma que el bot esté en el grupo

### Error al transcribir
- Verifica `TRANSCRIPTION_API_URL` en `.env`
- Confirma que la API esté funcionando

### Error al enviar queries
- Verifica `QUERY_SYSTEM_URL` en `.env`
- Revisa los logs para más detalles

---

## Notas

- Requiere Python 3.9+ para type hints modernos (`dict[str, int]`)
- El bot NO detiene el programa si hay errores, continúa procesando mensajes
- Los mensajes de error se envían como respuestas en Telegram
