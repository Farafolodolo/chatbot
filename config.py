### config.py
import os
from dotenv import load_dotenv

# Carga variables de entorno desde .env en desarrollo
load_dotenv()

class Settings:
    # URI de conexión a MongoDB (Atlas)
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    # Nombre de la base de datos
    DB_NAME: str = os.getenv("DB_NAME", "miDB")

settings = Settings()