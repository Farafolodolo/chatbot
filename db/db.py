from pymongo import MongoClient, TEXT, DESCENDING, errors
from pymongo.collection import Collection
from config import settings
from bson import ObjectId
import pytz
from datetime import datetime

class MongoDB:
    def __init__(self, uri: str, db_name: str):
        print("Esta es la URI: ", uri)
        print("Esta es la db: ", db_name)
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        
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

    def get_chat(self, id: str):
        col = self.get_collection("historial")
        query = {
            "_id": ObjectId(id)
        }
        result = col.find_one(query)
        if not result:
            return {}
        
        result["_id"] = str(result.get("_id", ""))

        return result
    
    def get_chats(self):
        col = self.get_collection("historial")
        cursor = col.find().sort("fecha_creada", DESCENDING).limit(10)
        chats = list(cursor)
        if len(chats) == 0:
            return []
        
        for chat in chats:
            chat["_id"] = str(chat.get("_id", ""))
            chat["fecha_creada"] = chat["fecha_creada"].isoformat()

        return chats
    
    def insert_chat(self):
        local_zone = pytz.timezone('America/Chihuahua')
        local_date = datetime.now(local_zone)

        col = self.get_collection("historial")
        query = {
            "fecha_creada": local_date,
            "chat": []
            }
        try:
            result = col.insert_one(query)
            chat_id = str(result.inserted_id)
            return chat_id
        except errors.DuplicateKeyError:
            return "duplicate"
        except errors.PyMongoError as e:
            print(f"Error inserting a new chat: {e}")
            return "no_inserted"
    
    def get_answers(self, topic, to_find):
        col = self.get_collection(topic)


        docs = list(col.find(
                {"$text": {"$search": to_find}},
            {
                "score": {"$meta": "textScore"},
                "respuesta": 1,
                "pregunta": 1
            }
        ).sort([("score", {"$meta": "textScore"})]).limit(5))

        if not docs:
            print("Did not take docs")
            return None
        
        return docs

    def update_chat(self, id, question, answer, error: bool):
        collection = self.get_collection("historial")
        chat_id = ObjectId(id)
        query = {
            "_id": chat_id
        }
        chat = collection.find_one(query)
        messages = chat["chat"]

        message = {
            "usuario": question,
            "bot": answer,
            "error": error
        }

        messages.append(message)

        if len(messages) > 25:
            messages = messages[-25]

        try:
            collection.update_one(
                {"_id": chat_id},
                {"$set": {"chat": messages}}
            )
            print("EVERYTHING WENT WELL WITH THE UPDATE")
            return True
        except:
            print("BRO, YOU DON'T EVEN KNOW HOW TO MAKE AN UPDATE")
            return False
        
    def get_questions_by_topic(self, topic: str):
        """Get all questions for a specific topic"""
        col = self.get_collection(topic)
        # Find all documents and extract only the questions
        cursor = col.find({}, {"pregunta": 1, "_id": 0})
        # Return list of questions
        return [doc["pregunta"] for doc in cursor]

mongodb = MongoDB(settings.MONGODB_URI, settings.DB_NAME)