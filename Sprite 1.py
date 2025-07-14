import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
import pyrebase
import firebase_admin
from firebase_admin import credentials, db, auth as admin_auth
import cloudinary
import cloudinary.uploader

# Configurar Cloudinary con tus credenciales
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key') # Use environment variable

# -------------------- CONFIGURACIÓN FIREBASE --------------------
firebase_config = {
    "apiKey": os.environ.get('FIREBASE_API_KEY'),
    "authDomain": os.environ.get('FIREBASE_AUTH_DOMAIN'),
    "databaseURL": os.environ.get('FIREBASE_DATABASE_URL'),
    "projectId": os.environ.get('FIREBASE_PROJECT_ID'),
    "storageBucket": os.environ.get('FIREBASE_STORAGE_BUCKET'),
    "messagingSenderId": os.environ.get('FIREBASE_MESSAGING_SENDER_ID'),
    "appId": os.environ.get('FIREBASE_APP_ID'),
    "measurementId": os.environ.get('FIREBASE_MEASUREMENT_ID')
}

# Inicializamos Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
pyre_auth = firebase.auth()

# Inicializamos Admin SDK para la base de datos
# AHORA LEEREMOS DE VARIABLES DE ENTORNO EN LUGAR DEL ARCHIVO JSON
try:
    # Asegúrate de que FIREBASE_PRIVATE_KEY tenga los saltos de línea correctos (\n)
    private_key = os.environ.get('FIREBASE_PRIVATE_KEY').replace('\\n', '\n')
    cred = credentials.Certificate({
        "type": os.environ.get('FIREBASE_TYPE'),
        "project_id": os.environ.get('FIREBASE_PROJECT_ID'),
        "private_key_id": os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
        "private_key": private_key,
        "client_email": os.environ.get('FIREBASE_CLIENT_EMAIL'),
        "client_id": os.environ.get('FIREBASE_CLIENT_ID'),
        "auth_uri": os.environ.get('FIREBASE_AUTH_URI'),
        "token_uri": os.environ.get('FIREBASE_TOKEN_URI'),
        "auth_provider_x509_cert_url": os.environ.get('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
        "client_x509_cert_url": os.environ.get('FIREBASE_CLIENT_X509_CERT_URL'),
        "universe_domain": os.environ.get('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com') # A veces esto es opcional o tiene un valor predeterminado
    })

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            "databaseURL": firebase_config["databaseURL"]
        })
    print("Firebase Admin SDK inicializado correctamente desde variables de entorno.")
except Exception as e:
    print(f"ERROR: No se pudo inicializar Firebase Admin SDK desde variables de entorno. Asegúrate de que todas las variables de entorno de Firebase Admin estén configuradas correctamente: {e}")
    # Opcional: Si quieres que la aplicación falle si no se puede inicializar Firebase
    # import sys
    # sys.exit(1)


if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "databaseURL": firebase_config["databaseURL"]
    })

# -------------------- RUTAS FLASK --------------------
@app.route('/')
def home():
    """ Página de inicio """
    return render_template("index.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            user = pyre_auth.sign_in_with_email_and_password(email, password)
            uid = user['localId']
            datos = db.reference(f'usuarios/{uid}').get()
            session['user'] = {'uid': uid, 'perfil': datos.get('perfil', 'Usuario')}
            print(f"✅ User logged in: {email}, UID: {uid}")  # <-- Añadir
            return redirect(url_for("inventario"))
        except Exception as e:
            print(f"❌ Login error: {e}")  # <-- Añadir para diagnosticar
            flash("Correo o contraseña incorrectos.")
    return render_template("login.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    """ Página de registro """
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        perfil = request.form.get("perfil")
        try:
            user = pyre_auth.create_user_with_email_and_password(email, password)
            uid = user['localId']
            db.reference(f'usuarios/{uid}').set({
                "email": email,
                "perfil": perfil
            })
            flash("Usuario registrado correctamente. Ahora inicia sesión.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error al crear usuario: {str(e)}", "error")
    return render_template("register.html")

@app.route('/inventario')
def inventario():
    """ Página de inventario """
    if 'user' not in session:
        return redirect(url_for("login"))
    uid = session['user']['uid']
    perfil = session['user']['perfil']
    productos = db.reference(f'usuarios/{uid}/productos').get() or {}
    print(f"✅ Inventario cargado para UID: {uid}")
    return render_template("inventario.html", perfil=perfil, productos=productos)

@app.route('/agregar_producto', methods=["POST"])
def agregar_producto():
    if 'user' not in session:
        return redirect(url_for("login"))
    uid = session['user']['uid']

    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    cantidad = request.form.get('cantidad')
    precio = request.form.get('precio')
    imagen = request.files.get('imagen')

    if nombre and cantidad.isdigit() and precio.replace('.', '', 1).isdigit():
        producto_data = {
            "nombre": nombre,
            "descripcion": descripcion,
            "cantidad": int(cantidad),
            "precio": float(precio)
        }

        # Subir imagen si se proporcionó
        if imagen and imagen.filename != "":
            result = cloudinary.uploader.upload(imagen)
            url_imagen = result['secure_url']
            producto_data["imagen_url"] = url_imagen
        else:
            # Keep existing image if no new one is uploaded during edit
            # This requires fetching the current product data.
            # For adding, if no image, just don't add imagen_url.
            pass

        db.reference(f'usuarios/{uid}/productos').push(producto_data)
        flash("Producto agregado correctamente.", "success")
    else:
        flash("Por favor ingresa datos válidos.", "error")

    return redirect(url_for("inventario"))

@app.route('/eliminar_producto/<producto_id>', methods=["POST"])
def eliminar_producto(producto_id):
    """ Elimina producto del inventario """
    if 'user' not in session:
        return redirect(url_for("login"))
    uid = session['user']['uid']
    db.reference(f'usuarios/{uid}/productos/{producto_id}').delete()
    flash("Producto eliminado correctamente.", "success")
    return redirect(url_for("inventario"))

@app.route('/editar_producto/<producto_id>', methods=["GET", "POST"])
def editar_producto(producto_id):
    if 'user' not in session:
        return redirect(url_for("login"))

    uid = session['user']['uid']
    producto_ref = db.reference(f'usuarios/{uid}/productos/{producto_id}')
    producto = producto_ref.get()

    if request.method == "POST":
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        cantidad = request.form.get('cantidad')
        precio = request.form.get('precio')
        imagen = request.files.get('imagen')  # Solo se define aquí dentro del POST

        if nombre and cantidad.isdigit() and precio.replace('.', '', 1).isdigit():
            data_update = {
                "nombre": nombre,
                "descripcion": descripcion,
                "cantidad": int(cantidad),
                "precio": float(precio)
            }

            # Solo se usa imagen si está definida
            if imagen and imagen.filename != "":
                result = cloudinary.uploader.upload(imagen)
                data_update["imagen_url"] = result['secure_url']
            # If no new image, and an old one exists, keep the old one.
            # If no new image and no old one, just don't add imagen_url.
            elif 'imagen_url' in producto: # If an existing image URL is present and no new file uploaded
                data_update["imagen_url"] = producto["imagen_url"] # Keep the old image URL

            producto_ref.update(data_update)
            flash("Producto actualizado correctamente.", "success")
            return redirect(url_for("inventario"))
        else:
            flash("Datos inválidos.", "error")

    # GET: solo renderiza el formulario sin usar 'imagen'
    return render_template("editar_producto.html", producto=producto, producto_id=producto_id)


@app.route('/logout')
def logout():
    """ Cierra la sesión """
    session.clear()
    return redirect(url_for("home"))

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)