"""Script helper para agregar usuarios/chats a la whitelist"""
import sys
import os
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.repositories.user_repository import UserRepository
from src.repositories.chat_repository import ChatRepository
from src.models.user import User
from src.models.chat import Chat


def add_user():
    """Agrega un usuario interactivamente"""
    print("\n=== Agregar Usuario a Whitelist ===\n")

    user_id = int(input("User ID: "))
    username = input("Username (opcional, Enter para omitir): ").strip() or None
    first_name = input("Nombre (opcional): ").strip() or None
    last_name = input("Apellido (opcional): ").strip() or None

    user = User(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_allowed=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    repo = UserRepository()
    repo.save(user)

    print(f"\n✅ Usuario {user_id} agregado a la whitelist!")


def add_chat():
    """Agrega un chat interactivamente"""
    print("\n=== Agregar Chat a Whitelist ===\n")

    chat_id = int(input("Chat ID: "))
    title = input("Título del chat (opcional): ").strip() or None

    print("\nTipo de chat:")
    print("1. private")
    print("2. group")
    print("3. supergroup")
    print("4. channel")
    chat_type_choice = input("Selecciona (1-4): ").strip()

    chat_types = {
        "1": "private",
        "2": "group",
        "3": "supergroup",
        "4": "channel"
    }
    chat_type = chat_types.get(chat_type_choice, "private")

    chat = Chat(
        chat_id=chat_id,
        title=title,
        type=chat_type,
        is_allowed=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    repo = ChatRepository()
    repo.save(chat)

    print(f"\n✅ Chat {chat_id} agregado a la whitelist!")


def list_users():
    """Lista todos los usuarios"""
    repo = UserRepository()
    users = repo.get_all()

    print("\n=== Usuarios en Whitelist ===\n")

    if not users:
        print("No hay usuarios en la whitelist")
        return

    for user in users:
        status = "✅" if user.is_allowed else "❌"
        print(f"{status} {user.user_id} - {user.get_display_name()} (@{user.username})")


def list_chats():
    """Lista todos los chats"""
    repo = ChatRepository()
    chats = repo.get_all()

    print("\n=== Chats en Whitelist ===\n")

    if not chats:
        print("No hay chats en la whitelist")
        return

    for chat in chats:
        status = "✅" if chat.is_allowed else "❌"
        print(f"{status} {chat.chat_id} - {chat.get_display_name()} ({chat.type})")


def main():
    """Menú principal"""
    while True:
        print("\n" + "="*50)
        print("Gestión de Whitelist")
        print("="*50)
        print("1. Agregar usuario")
        print("2. Agregar chat")
        print("3. Listar usuarios")
        print("4. Listar chats")
        print("5. Salir")
        print("="*50)

        choice = input("\nSelecciona una opción: ").strip()

        if choice == "1":
            add_user()
        elif choice == "2":
            add_chat()
        elif choice == "3":
            list_users()
        elif choice == "4":
            list_chats()
        elif choice == "5":
            print("\n¡Adiós!")
            break
        else:
            print("\n❌ Opción inválida")


if __name__ == "__main__":
    main()
