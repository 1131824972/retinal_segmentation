from datetime import datetime
from core.database import users_collection
from bson.objectid import ObjectId

class User:
    def __init__(self, username: str, password_hash: str, email: str):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def save(self):
        user_data = self.__dict__
        result = users_collection.insert_one(user_data)
        return str(result.inserted_id)

    @classmethod
    def find_by_email(cls, email: str):
        data = users_collection.find_one({"email": email})
        return data

    @classmethod
    def find_by_id(cls, user_id: str):
        data = users_collection.find_one({"_id": ObjectId(user_id)})
        return data
