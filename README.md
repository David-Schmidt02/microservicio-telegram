# Microservicio de Telegram - Procesador de Audio y Texto

Microservicio en Python que procesa mensajes de audio y texto en grupos de Telegram. Los audios se transcriben usando una API externa y tanto las transcripciones como los mensajes de texto se envían a un sistema de queries para obtener respuestas inteligentes.

## Características

- Bot de Telegram con polling cada 2-3 segundos (configurable)
- Detección automática de mensajes de audio/voz y texto
- Transcripción de audio mediante API externa
- Procesamiento asíncrono con asyncio y aiohttp
- Manejo de sesiones por grupo de Telegram
- **Sistema de whitelist** para usuarios y chats (YAML → SQLite → SQL)
- **División automática de mensajes largos** que exceden el límite de 4096 caracteres de Telegram
- **Formateo inteligente de incidentes** desde respuestas del MCP server de búsqueda
- Validación de datos con Pydantic
- Logging detallado con niveles configurables
- Limpieza automática de archivos temporales
- Arquitectura preparada para migración de persistencia

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

### 4. Configurar Whitelist (Control de Acceso)

El bot solo procesa mensajes de usuarios y chats autorizados. Para configurar:

**Opción A: Usando el script helper (recomendado)**
```bash
python scripts/add_to_whitelist.py
```
Sigue las opciones del menú interactivo para agregar usuarios y chats.

**Opción B: Editando YAML manualmente**

1. Copia los archivos de ejemplo:
```bash
cp data/users.yaml.example data/users.yaml
cp data/chats.yaml.example data/chats.yaml
```

2. Edita `data/users.yaml` y agrega tus usuarios:
```yaml
users:
  - user_id: 123456789  # Tu Telegram user ID
    username: "tu_usuario"
    first_name: "Tu Nombre"
    is_allowed: true
    created_at: "2025-10-16T14:00:00"
    updated_at: "2025-10-16T14:00:00"
```

3. Edita `data/chats.yaml` y agrega tus chats/grupos:
```yaml
chats:
  - chat_id: -1001234567890  # ID de tu grupo
    title: "Mi Grupo"
    type: "supergroup"
    is_allowed: true
    created_at: "2025-10-16T14:00:00"
    updated_at: "2025-10-16T14:00:00"
```

**¿Cómo obtengo los IDs?**
- Ejecuta el bot sin configurar whitelist
- Envía un mensaje
- Revisa los logs: verás los user_id y chat_id que intentaron acceder

Ver `data/README.md` para más detalles.

### 5. Ejecutar

```bash
python main.py
```

---

## Estructura del Proyecto

```
microservicio-telegram/
├── src/
│   ├── bot.py                          # Orquestador principal (TelegramAudioBot)
│   ├── schemas.py                      # DTOs de Telegram (Pydantic)
│   ├── models/                         # 🆕 Modelos de dominio
│   │   ├── user.py                     #   - Entidad User
│   │   └── chat.py                     #   - Entidad Chat
│   ├── repositories/                   # 🆕 Capa de persistencia
│   │   ├── base_repository.py          #   - Interfaz abstracta
│   │   ├── user_repository.py          #   - Implementación YAML para users
│   │   └── chat_repository.py          #   - Implementación YAML para chats
│   ├── services/
│   │   ├── telegram_service.py         # Cliente de Telegram API (async)
│   │   ├── transcription_service.py    # Servicio de transcripción (async)
│   │   ├── query_service.py            # Servicio de queries (async)
│   │   └── authorization_service.py    # 🆕 Lógica de whitelist
│   ├── config/
│   │   └── settings.py                 # Configuración centralizada
│   └── utils/
│       ├── logger.py                   # Configuración de logging
│       ├── error_handler.py            # Decorador de manejo de errores
│       └── retry.py                    # 🆕 Helper de reintentos async
├── data/                               # 🆕 Persistencia (YAML)
│   ├── users.yaml                      #   - Whitelist de usuarios
│   ├── chats.yaml                      #   - Whitelist de chats
│   ├── users.yaml.example              #   - Ejemplo de users
│   ├── chats.yaml.example              #   - Ejemplo de chats
│   └── README.md                       #   - Documentación
├── scripts/                            # 🆕 Scripts de utilidad
│   └── add_to_whitelist.py             #   - Gestión interactiva de whitelist
├── temp_audio/                         # Archivos temporales (auto-creado)
├── main.py                             # Punto de entrada
├── requirements.txt
└── README.md
```

---

## Arquitectura

### Patrón de Capas

```
main.py
    ↓
TelegramAudioBot (Application Service / Orquestador)
    ↓
┌──────────────┬───────────────┬────────────┬────────────────────┐
│  Telegram    │Transcription  │   Query    │  Authorization     │
│  Service     │  Service      │  Service   │  Service           │
└──────────────┴───────────────┴────────────┴─────────┬──────────┘
                                                       ↓
                                            ┌──────────────────────┐
                                            │  Repository Layer     │
                                            │  (UserRepo, ChatRepo) │
                                            └──────────┬────────────┘
                                                       ↓
                                            ┌──────────────────────┐
                                            │   Persistencia        │
                                            │  (YAML → SQLite → SQL)│
                                            └───────────────────────┘
```

**Capas:**
- **Application Service**: Orquesta los servicios (TelegramAudioBot)
- **Service Layer**: Lógica de negocio (validación, transformación)
- **Repository Layer**: Abstracción de persistencia (cambiar fácilmente entre YAML/SQLite/SQL)
- **Persistencia**: Almacenamiento de datos

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
    ↓ Respuesta: {"transcription": "texto transcrito"}
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
    ↓ Response: {"answer": "...", "mcp_server_used": "...", "metadata": {...}}
    ↓
【PROCESAMIENTO DE RESPUESTA】
_get_search_incidents(result)
    ↓ Verifica si mcp_server_used == 'search'
    ↓ Extrae metadata.results.incidentes si existen
    ↓
Si hay incidentes:
    ↓ Envía resumen (primeros ~60 chars)
    ↓ Envía cada incidente formateado individualmente

Si NO hay incidentes:
    ↓ Envía respuesta normal con el answer completo
    ↓
【DIVISIÓN AUTOMÁTICA SI ES NECESARIO】
Si el mensaje supera 4096 caracteres:
    ↓ _split_by_incidents() divide por "---"
    ↓ _send_message_parts() envía cada parte con pausa de 0.5s
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
  "transcription": "Texto transcrito del audio"
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
  "answer": "Respuesta del sistema",
  "mcp_server_used": "search",
  "metadata": {
    "results": {
      "incidentes": [
        {
          "descripcion": "...",
          "fecha": "2025-10-17",
          "horario_exacto": "12:44:13.857-03:00",
          "direccion": "Calle X, 1234",
          "barrio": "BARRIO",
          "comuna": "COMUNA 1",
          "comisaria": "CRIA VECINAL 1A",
          "comentarios": "..."
        }
      ]
    }
  }
}
```

**Nota:** El campo `metadata.results.incidentes` es opcional y solo está presente cuando `mcp_server_used == 'search'`. En ese caso, el bot formatea y envía cada incidente como mensaje separado.

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

### Manejo de Mensajes Largos

El bot maneja automáticamente respuestas que exceden el límite de 4096 caracteres de Telegram:

1. **División por separadores**: `_split_by_incidents(text)` divide el mensaje usando "---" como separador
2. **Envío secuencial**: `_send_message_parts(parts)` envía cada parte con pausa de 0.5s
3. **Reply solo en primera parte**: Solo el primer mensaje responde (reply) al mensaje original del usuario
4. **Logging**: Registra cuántas partes se enviaron

### Formateo de Incidentes

Cuando el sistema de queries usa el MCP server "search" y retorna incidentes:

1. **Detección**: `_get_search_incidents(result)` verifica `mcp_server_used == 'search'` y extrae `metadata.results.incidentes`
2. **Resumen**: Envía los primeros ~60 caracteres del `answer` como resumen
3. **Formateo individual**: `_format_incident(incidente, numero)` formatea cada incidente con:
   - Número de incidente
   - Descripción
   - Fecha y hora exacta
   - Ubicación (dirección, barrio, comuna)
   - Comisaría (si existe)
   - Comentarios adicionales (si existen)
4. **Envío separado**: Cada incidente se envía como mensaje individual

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

### Error 400 Bad Request al enviar mensajes
- El bot ahora divide automáticamente mensajes largos por "---"
- Si aún falla, verifica que cada incidente individual no exceda 4096 caracteres
- Revisa los logs para ver cuántas partes se intentaron enviar

### Los incidentes no se muestran formateados
- Verifica que el query system retorne `mcp_server_used: "search"`
- Confirma que existe el campo `metadata.results.incidentes` en la respuesta
- Revisa los logs para ver si `_get_search_incidents()` encontró incidentes

---

## Notas

- Requiere Python 3.9+ para type hints modernos (`dict[str, int]`)
- El bot NO detiene el programa si hay errores, continúa procesando mensajes
- Los mensajes de error se envían como respuestas en Telegram
