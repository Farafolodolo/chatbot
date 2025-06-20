from pymongo import MongoClient, TEXT
from pymongo.collection import Collection
from config import settings

class MongoDB:
    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        # Verifica conexión al servidor
        self.client.admin.command('ping')

    def get_collection(self, tema: str) -> Collection:
        return self.db[tema]

    def ensure_text_index(self, tema: str):
        col = self.get_collection(tema)
        col.create_index(
            [("pregunta", TEXT), ("tags", TEXT)],
            default_language="spanish",
            name=f"TextIndex_{tema}"
        )

mongodb = MongoDB(settings.MONGODB_URI, settings.DB_NAME)