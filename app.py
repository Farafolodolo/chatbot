from flask import Flask
from routes import bp
from flask.json.provider import DefaultJSONProvider
from bson import ObjectId

app = Flask(__name__)

app.register_blueprint(bp)



class CustomJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

if __name__ == "__main__":
    app.run(port=5000, debug=True)