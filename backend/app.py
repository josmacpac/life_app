import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)

raw_cors = (
    os.environ.get("CORS_ORIGINS")
    or "http://localhost/life_app"
)
cors_origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

nuevo_dominio = "http://localhost/life_app"
if nuevo_dominio not in cors_origins:
    cors_origins.append(nuevo_dominio)

CORS(
    app,
    resources={r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
    }},
)

# --------------------------------------------------
# REGISTRO DE RUTAS (BLUEPRINTS)
# --------------------------------------------------
from routes.sessions import sessions_pb

app.register_blueprint(sessions_pb, url_prefix="/api/sessions")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)
