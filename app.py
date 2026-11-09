# app.py
# PUNTO DE ENTRADA: aquí se crea la aplicación Flask y se registra el Blueprint.

from flask import Flask

from controllers.polizas_controller import bp

# VARIABLE: la app. Las carpetas se indican tal como pide AGENTS.md.
app = Flask(
    __name__,
    template_folder="views",
    static_folder="public/static",
    static_url_path="/static",
)

# REGISTRO: conectamos las rutas del controlador con la app.
app.register_blueprint(bp)

# CONDICIONAL: solo arranca el servidor si ejecutamos este archivo directamente.
if __name__ == "__main__":
    app.run(debug=True, port=5000)
