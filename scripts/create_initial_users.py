import json
from pathlib import Path

from src.infrastructure.security.pbkdf2_password_hasher import Pbkdf2PasswordHasher


def main() -> None:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    hasher = Pbkdf2PasswordHasher()

    users = [
        {
            "username": "admin",
            "full_name": "Administrador Plataforma",
            "role": "admin",
            "password_hash": hasher.hash_password("Admin123!"),
            "is_active": True,
        },
        {
            "username": "analista1",
            "full_name": "Analista Cumplimiento 1",
            "role": "analyst",
            "password_hash": hasher.hash_password("Analista123!"),
            "is_active": True,
        },
        {
            "username": "analista2",
            "full_name": "Analista Cumplimiento 2",
            "role": "analyst",
            "password_hash": hasher.hash_password("Analista456!"),
            "is_active": True,
        },
    ]

    output_path = data_dir / "users.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(users, file, indent=2, ensure_ascii=False)

    print(f"Usuarios creados en {output_path}")


if __name__ == "__main__":
    main()
