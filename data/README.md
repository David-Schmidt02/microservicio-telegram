# Whitelist de Usuarios y Chats

Esta carpeta contiene los archivos YAML que definen qué usuarios y chats están autorizados para usar el bot.

## Archivos

- `users.yaml` - Lista de usuarios autorizados
- `chats.yaml` - Lista de chats/grupos autorizados
- `users.yaml.example` - Ejemplo de formato para usuarios
- `chats.yaml.example` - Ejemplo de formato para chats

## Cómo autorizar un usuario

1. **Obtener el user_id:**
   - Haz que el usuario envíe un mensaje al bot
   - Revisa los logs, verás algo como:
     ```
     WARNING - Usuario 123456789 no existe en la whitelist
     ```

2. **Agregar al whitelist:**
   - Edita `data/users.yaml`
   - Agrega el usuario con este formato:
   ```yaml
   users:
     - user_id: 123456789
       username: "nombre_usuario"
       first_name: "Nombre"
       last_name: "Apellido"
       is_allowed: true
       created_at: "2025-10-16T14:00:00"
       updated_at: "2025-10-16T14:00:00"
   ```

3. **Reiniciar el bot** (no es necesario si se implementa hot-reload en el futuro)

## Cómo autorizar un chat/grupo

1. **Obtener el chat_id:**
   - Envía un mensaje en el grupo al bot
   - Revisa los logs, verás algo como:
     ```
     WARNING - Chat -4871163359 no existe en la whitelist
     ```

2. **Agregar al whitelist:**
   - Edita `data/chats.yaml`
   - Agrega el chat con este formato:
   ```yaml
   chats:
     - chat_id: -4871163359
       title: "Nombre del Grupo"
       type: "supergroup"  # puede ser: private, group, supergroup, channel
       is_allowed: true
       created_at: "2025-10-16T14:00:00"
       updated_at: "2025-10-16T14:00:00"
   ```

3. **Reiniciar el bot**

## Notas importantes

- **Los user_id son permanentes** para cada bot y nunca cambian
- **Los chat_id son estables**:
  - Positivos para chats privados
  - Negativos para grupos y supergrupos
- **El username puede cambiar**, por eso siempre identificamos por ID
- Los archivos `*.yaml` son ignorados por git (no se subirán al repositorio)
- Solo los archivos `*.example` se suben como referencia

## Migración futura

Esta estructura con YAML es temporal. En el futuro migraremos a:
1. SQLite (base de datos local)
2. PostgreSQL/MySQL (base de datos en servidor)

Gracias al patrón Repository, cambiar la implementación será transparente para el resto del código.
