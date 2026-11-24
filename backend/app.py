import os
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
from supabase import create_client, Client
from flask_cors import CORS
from extensions import limiter



# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Inicializar el rate limiter
limiter.init_app(app)

# CORS restringido: solo los orígenes permitidos explícitamente.
# Sobrescribe con la variable CORS_ORIGINS (separada por comas) si cambian los dominios.
# CORS restringido: lee del entorno o usa la lista base, y asegura el nuevo Netlify
raw_cors = (
    os.environ.get("CORS_ORIGINS")
or "http://localhost/life_app"
)

cors_origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

# Forzar el nuevo dominio de Netlify por si la variable de entorno del servidor lo oculta
nuevo_dominio = "http://localhost/life_app"
if nuevo_dominio not in cors_origins:
    cors_origins.append(nuevo_dominio)

CORS(
    app,
    resources={r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Clinica-Id", "X-Deploy-Key"],
        "supports_credentials": True,
    }},
)


# --------------------------------------------------
# REGISTRO DE RUTAS (BLUEPRINTS)
# --------------------------------------------------
from routes.test import test_pb
from routes.articulos import articulos_pb


app.register_blueprint(test_pb, url_prefix='/api')
app.register_blueprint(articulos_pb, url_prefix='/api')
app.register_blueprint(proveedores_pb, url_prefix='/api')



if __name__ == '__main__':
    # Debug NUNCA en producción. Usa FLASK_DEBUG=1 solo en tu máquina de desarrollo.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)

