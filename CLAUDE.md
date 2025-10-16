# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python microservice that processes Telegram messages (text and audio/voice) and sends them to a query system. Audio messages are first transcribed using an external API before being sent to the query system.

## Common Commands

### Running the Service
```bash
python main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Setting up Environment
Copy `.env.example` to `.env` and configure the required variables:
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Chat/group ID to monitor
- `TRANSCRIPTION_API_URL` - URL of transcription service
- `QUERY_SYSTEM_URL` - URL of query processing system
- `POLLING_INTERVAL` - Polling interval in seconds (default: 2.5)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Architecture

### Service Layer Pattern
The codebase follows a modular service architecture with clear separation of concerns:

- **TelegramService** (`src/services/telegram_service.py`): Handles all Telegram API interactions including polling, message extraction, audio download, and message sending. Uses raw requests API instead of python-telegram-bot wrapper.

- **TranscriptionService** (`src/services/transcription_service.py`): Manages audio transcription via external API. Expects response with `transcription`, `text`, or `transcript` field.

- **QueryService** (`src/services/query_service.py`): Sends queries to the external system with payload format: `{"question": str, "session_id": str}`. Expects response with `answer` field.

- **UserService** (`src/services/user_service.py`): Mentioned in git status but not yet in main flow.

### Message Processing Flow

1. **Polling Loop**: TelegramService polls every 2-3 seconds (configurable) using `getUpdates` API
2. **Message Classification**: Updates are classified into audio messages or text messages
3. **Audio Processing** (for voice/audio messages):
   - Download audio file to `temp_audio/` directory
   - Send to TranscriptionService
   - Pass transcription to QueryService
   - Clean up temporary audio file
4. **Text Processing** (for text messages):
   - Send directly to QueryService
5. **Response**: Bot replies to original message with query result

### Pydantic Schema Models

The codebase uses Pydantic for data validation (`src/schemas.py`):

- **TelegramUser**: User information (ID, username, names, language)
- **TelegramChat**: Chat information (ID, type, title)
- **TelegramTextMessage**: Text message with user and chat context
- **TelegramAudioMessage**: Audio message with file_id, duration, and context

All message models have `from_telegram_update()` class methods to parse raw Telegram API responses.

### Session Management

Session IDs are generated per chat: `telegram-group-{chat_id}` to maintain conversation context in the query system across multiple users in the same group.

### Configuration

Centralized in `src/config/settings.py` using environment variables loaded via python-dotenv. The `Settings.validate()` method ensures all required variables are present before startup.

### Logging

Consistent logging setup via `src/utils/logger.py` with configurable log levels. All services use structured logging with module names for traceability.

## Important Implementation Details

- The bot uses **manual polling** (not webhooks) with `getUpdates` API
- Audio files are temporarily stored in `temp_audio/` and cleaned up after processing
- The service handles both `voice` (voice messages) and `audio` (audio files) from Telegram
- API key headers are currently commented out in all services (lines with `#self.api_key`)
- Response format flexibility: transcription API can return field named `transcription`, `text`, or `transcript`
- Error responses are sent back to Telegram as replies to the original message
- The main bot class (`TelegramAudioBot` in `main.py`) orchestrates all services via async callback pattern
