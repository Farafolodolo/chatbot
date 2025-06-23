### config.py
import os
import dotenv

# Carga variables de entorno desde .env en desarrollo
dotenv.load_dotenv()

class Settings:
    # URI de conexión a MongoDB (Atlas)
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    # Nombre de la base de datos
    DB_NAME: str = os.getenv("DB_NAME", "miDB")

    HF_TOKEN: str = os.getenv("HF_TOKEN","")

settings = Settings()