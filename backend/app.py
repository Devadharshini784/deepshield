from flask import Flask
from flask_cors import CORS
from modules.auth.routes import auth_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")

@app.route("/")
def home():
    return {"message": "DeepShield backend is running"}

if __name__ == "__main__":
    app.run(debug=True, port=5000)