
from flask import Flask, jsonify, request, url_for
import os
import psycopg2
import hashlib
import json
from html import escape
from pathlib import Path


app = Flask(__name__)

# Detectar si estamos en entorno de desarrollo o producción
APP_ENV = os.getenv("APP_ENV", "dev")  # Por defecto será dev


# ---------- MENÚ DE NAVEGACIÓN ----------

# Menú común para todas las páginas HTML.
# La opción Redis solo aparece en producción.
MENU = """
<nav style="background:#24364b; padding:15px;">
    <a href="/" style="color:white; margin-right:20px;">Inicio</a>
    <a href="/form" style="color:white; margin-right:20px;">Formulario</a>
    <a href="/list" style="color:white; margin-right:20px;">Registros</a>
    <a href="/status" style="color:white; margin-right:20px;">Estado</a>
    {redis_link}
</nav>
""".replace(
    "{redis_link}",
    '<a href="/cache-test" style="color:white;">Redis</a>'
    if APP_ENV == "prod" else ""
)


# ---------- CONFIGURACIÓN DEL ENTORNO ----------

# En producción guardamos la imagen estática en la caché del navegador
# durante una hora para reducir las descargas repetidas.
if APP_ENV == "prod":
    print("Modo PRODUCCIÓN: con imagen y caché activados")
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600

    @app.after_request
    def add_cache_headers(resp):
        if request.path.startswith("/static/"):
            resp.headers["Cache-Control"] = "public, max-age=3600, must-revalidate"
        return resp
else:
    print("Modo DESARROLLO: sin caché ni imagen")


# ---------- PÁGINA PRINCIPAL ----------

@app.route("/")
def home():
    return f"""
    <html>
      <body style="font-family: sans-serif; margin:0;">
        {MENU}

        <div style="max-width:640px; margin:40px auto;">
          <h2>Práctica 1 - Docker</h2>
          <p>Hola! La aplicación Flask está funcionando.</p>
          <p>Entorno actual: <strong>{APP_ENV.upper()}</strong></p>
        </div>
      </body>
    </html>
    """


# ---------- CONEXIÓN POSTGRESQL ----------

# Comprueba si PostgreSQL está disponible.
# Se utiliza desde /status para verificar el estado de la BD.
def db_conn_ok():
    try:
        conn = psycopg2.connect(
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=os.environ.get("DB_PORT", "5432"),
            connect_timeout=2
        )
        conn.close()
        return True
    except Exception:
        return False


# ---------- CONEXIÓN REDIS ----------

# Redis solo se configura en producción.
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

r = None

if REDIS_HOST:
    try:
        import redis

        r = redis.Redis(
            host=REDIS_HOST,
            port=int(REDIS_PORT),
            socket_connect_timeout=2,
            socket_timeout=2
        )

        r.ping()
        print("Conectado a Redis correctamente")

    except Exception as e:
        print(f"No se pudo conectar a Redis: {e}")
        # Mantenemos el cliente si se ha creado para permitir
        # que vuelva a conectar cuando Redis esté disponible.


# ---------- ESTADO DE LOS SERVICIOS ----------

# Endpoint utilizado por los healthchecks de Docker.
@app.route("/status")
def status():
    db_ok = db_conn_ok()

    cache_ok = False

    if r is not None:
        try:
            r.ping()
            cache_ok = True
        except Exception:
            cache_ok = False

    return jsonify({
        "db_connected": db_ok,
        "cache_connected": cache_ok
    })


# ---------- PRUEBA DE REDIS ----------

# Incrementa un contador almacenado en Redis.
# Sirve para demostrar que Flask puede leer y escribir en Redis.
@app.route("/cache-test")
def cache_test():
    if r is None:
        return jsonify({
            "ok": False,
            "msg": "Redis no configurado"
        })

    try:
        visitas = r.incr("visitas")

        return jsonify({
            "ok": True,
            "visitas": int(visitas)
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 503


# ---------- FORMULARIO ----------

@app.route("/form")
def form():
    logo_html = ""

    # En producción mostramos una imagen.
    if APP_ENV == "prod":
        STATIC_DIR = Path(__file__).parent / "static"

        # Calculamos un hash para actualizar la imagen del navegador
        # cuando se modifica el archivo original.
        def file_hash(path: Path) -> str:
            try:
                with open(path, "rb") as f:
                    return hashlib.md5(f.read()).hexdigest()[:8]
            except FileNotFoundError:
                return "1"

        LOGO_VER = file_hash(STATIC_DIR / "logo.png")
        logo_url = url_for("static", filename="logo.png") + f"?v={LOGO_VER}"

        logo_html = f"""
        <img src="{logo_url}" alt="Logo" width="80"
             style="border-radius:8px; margin-right:16px;">
        """

    return f"""
    <html>
      <body style="font-family:sans-serif; margin:0;">
        {MENU}

        <div style="max-width:420px; margin:40px auto;">
          <div style="display:flex; align-items:center; gap:16px;">
            {logo_html}
            <h3>Registro</h3>
          </div>

          <form method="POST" action="/submit" style="margin-top:20px;">
            <label>Nombre</label><br/>
            <input name="name" required/><br/><br/>

            <label>Apellido</label><br/>
            <input name="surname" required/><br/><br/>

            <label>Edad</label><br/>
            <input name="age" type="number" min="0" required/><br/><br/>

            <button type="submit">Enviar</button>
          </form>

          <p style="margin-top:16px;">
            <a href="/list">Ver últimos</a>
          </p>
        </div>
      </body>
    </html>
    """


# ---------- GUARDAR REGISTROS ----------

@app.route("/submit", methods=["POST"])
def submit():
    name = (request.form.get("name") or "").strip()
    surname = (request.form.get("surname") or "").strip()
    age_str = request.form.get("age") or "0"

    # Validación básica de los datos introducidos.
    try:
        age = int(age_str)
        if age < 0:
            raise ValueError()
    except ValueError:
        return jsonify({
            "ok": False,
            "error": "Edad inválida"
        }), 400

    if not name or not surname:
        return jsonify({
            "ok": False,
            "error": "Nombre y apellido son obligatorios"
        }), 400

    try:
        # Conexión con PostgreSQL.
        conn = psycopg2.connect(
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=os.environ.get("DB_PORT", "5432"),
            connect_timeout=3
        )

        try:
            # Guardamos el registro en PostgreSQL.
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users(name, surname, age) "
                        "VALUES (%s, %s, %s);",
                        (name, surname, age)
                    )
        finally:
            conn.close()

        # CACHE INVALIDATION:
        # Si se ha guardado un registro correctamente,
        # eliminamos los resultados antiguos de Redis.
        # La siguiente visita a /list consultará PostgreSQL
        # y volverá a guardar los datos actualizados en Redis.
        if APP_ENV == "prod" and r is not None:
            try:
                r.delete("ultimos_usuarios")
                print("Cache de usuarios invalidada")
            except Exception as e:
                print(f"Error invalidando cache: {e}")

        return f"""
        <html>
          <body style="font-family:sans-serif; margin:0;">
            {MENU}

            <div style="max-width:420px; margin:40px auto;">
              <p>Guardado correctamente.</p>
              <p>
                <a href="/form">Volver</a> ·
                <a href="/list">Ver últimos</a>
              </p>
            </div>
          </body>
        </html>
        """

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


# ---------- LISTA DE REGISTROS CON CACHÉ ----------

@app.route("/list")
def list_people():
    rows = None
    origen = "PostgreSQL"

    # CACHE HIT:
    # En producción comprobamos primero si Redis tiene
    # almacenados los últimos usuarios.
    if APP_ENV == "prod" and r is not None:
        try:
            datos_cache = r.get("ultimos_usuarios")

            if datos_cache is not None:
                # Recuperamos los resultados directamente de Redis.
                rows = json.loads(datos_cache)
                origen = "Redis (HIT)"

        except Exception as e:
            print(f"Error consultando Redis: {e}")

    # CACHE MISS:
    # Si Redis no tiene los datos (o estamos en DEV),
    # ejecutamos la consulta en PostgreSQL.
    if rows is None:
        try:
            conn = psycopg2.connect(
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                host=os.environ["DB_HOST"],
                port=os.environ.get("DB_PORT", "5432"),
                connect_timeout=3
            )

            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT id, name, surname, age, created_at "
                            "FROM users ORDER BY id DESC LIMIT 10;"
                        )
                        datos = cur.fetchall()
            finally:
                conn.close()

            # Convertimos los resultados SQL en una lista JSON.
            # Las fechas se convierten a texto para poder guardarlas.
            rows = [
                [id, name, surname, age, str(created_at)]
                for id, name, surname, age, created_at in datos
            ]

        except Exception as e:
            return jsonify({
                "ok": False,
                "error": str(e)
            }), 500

        # Guardamos los registros en Redis SIN CADUCIDAD.
        # Permanecerán en caché hasta que:
        # - Una inserción mediante /submit invalide la clave.
        # - Redis elimine o pierda los datos.
        if APP_ENV == "prod" and r is not None:
            try:
                r.set("ultimos_usuarios", json.dumps(rows))
                origen = "PostgreSQL (MISS)"
                print("Datos de PostgreSQL guardados en Redis")

            except Exception as e:
                print(f"Error guardando cache: {e}")

    # Generamos el HTML de la lista.
    # Escape evita interpretar nombres o apellidos como HTML.
    items = "".join(
        f"<li>#{row[0]} — {escape(str(row[1]))} "
        f"{escape(str(row[2]))} ({row[3]}) · "
        f"{escape(str(row[4]))}</li>"
        for row in rows
    ) or "<li>(sin datos)</li>"

    return f"""
    <html>
      <body style="font-family:sans-serif; margin:0;">
        {MENU}

        <div style="max-width:640px; margin:40px auto;">
          <h3>Últimos registros</h3>

          <p>
            <strong>Origen de los datos:</strong> {origen}
          </p>

          <ul>{items}</ul>

          <p><a href="/form">Nuevo registro</a></p>
        </div>
      </body>
    </html>
    """


# ---------- INICIO DE FLASK ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
