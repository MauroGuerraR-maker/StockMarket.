import os
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify 
import pyrebase
import firebase_admin
from firebase_admin import credentials, db, auth as admin_auth
import cloudinary
import cloudinary.uploader
import logging 
from datetime import datetime 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

# Configurar Cloudinary con tus credenciales (MANTÉN os.environ.get)
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key') 

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
try:
    # Asegúrate de que FIREBASE_ADMIN_PRIVATE_KEY (o el nombre que uses) tenga los saltos de línea correctos (\n)
    private_key_value = os.environ.get('FIREBASE_ADMIN_PRIVATE_KEY', '').replace('\\n', '\n') # Nombres consistentes

    # Crea el diccionario de credenciales a partir de las variables de entorno
    admin_credentials_data = {
        "type": os.environ.get('FIREBASE_ADMIN_TYPE'), # Nombres consistentes
        "project_id": os.environ.get('FIREBASE_ADMIN_PROJECT_ID'), # Nombres consistentes
        "private_key_id": os.environ.get('FIREBASE_ADMIN_PRIVATE_KEY_ID'), # Nombres consistentes
        "private_key": private_key_value,
        "client_email": os.environ.get('FIREBASE_ADMIN_CLIENT_EMAIL'), # Nombres consistentes
        "client_id": os.environ.get('FIREBASE_ADMIN_CLIENT_ID'), # Nombres consistentes
        "auth_uri": os.environ.get('FIREBASE_ADMIN_AUTH_URI'), # Nombres consistentes
        "token_uri": os.environ.get('FIREBASE_ADMIN_TOKEN_URI'), # Nombres consistentes
        "auth_provider_x509_cert_url": os.environ.get('FIREBASE_ADMIN_AUTH_PROVIDER_X509_CERT_URL'), # Nombres consistentes
        "client_x509_cert_url": os.environ.get('FIREBASE_ADMIN_CLIENT_X509_CERT_URL'), # Nombres consistentes
        "universe_domain": os.environ.get('FIREBASE_ADMIN_UNIVERSE_DOMAIN', 'googleapis.com')
    }

    # **AÑADE ESTA VALIDACIÓN:**
    # Verifica que todas las variables esenciales para el Admin SDK no sean None o cadenas vacías
    required_admin_keys = [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id", "auth_uri", "token_uri",
        "auth_provider_x509_cert_url", "client_x509_cert_url"
    ]
    for key in required_admin_keys:
        if not admin_credentials_data.get(key):
            raise ValueError(f"La variable de entorno FIREBASE_ADMIN_{key.upper()} no está configurada o está vacía.")


    cred = credentials.Certificate(admin_credentials_data)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            "databaseURL": firebase_config["databaseURL"]
        })
    print("Firebase Admin SDK inicializado correctamente desde variables de entorno.")
except Exception as e:
    print(f"ERROR: No se pudo inicializar Firebase Admin SDK desde variables de entorno. Asegúrate de que todas las variables de entorno de Firebase Admin estén configuradas correctamente. Error: {e}")
    # Si no se puede inicializar Firebase Admin, la aplicación no debería funcionar
    import sys
    sys.exit(1) # <-- Esto detendrá el despliegue si hay un problema

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
            # Fetch the company name to display in the inventory page
            datos = db.reference(f'usuarios/{uid}/empresa').get()
            # Ensure datos is treated as a dict for .get()
            session['user'] = {'uid': uid, 'nombre_empresa': datos.get('nombre_empresa', 'Empresa') if datos else 'Empresa'}
            logging.info(f"User logged in: {email}, UID: {uid}")
            return redirect(url_for("inventario"))
        except Exception as e:
            logging.error(f"Login error for {email}: {e}")
            flash("Correo o contraseña incorrectos.")
    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    """ Página de registro """
    if request.method == "POST":
        # Empresa Data
        nombre_empresa = request.form.get("nombre_empresa")
        nit = request.form.get("nit")
        numero_contacto = request.form.get("numero_contacto")
        direccion = request.form.get("direccion")
        logo_empresa = request.files.get("logo_empresa")

        # Representante Legal Data
        nombre_representante = request.form.get("nombre_representante")
        numero_identificacion = request.form.get("numero_identificacion")
        email = request.form.get("email")
        password = request.form.get("password")

        logging.info(f"Attempting to register: {email}")
        logging.info(f"Empresa: {nombre_empresa}, NIT: {nit}")
        logging.info(f"Representante: {nombre_representante}")


        # Basic validation for password length
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            logging.warning("Password too short during registration attempt.")
            return render_template("register.html")

        try:
            # Create user with email and password in Firebase Auth
            logging.info(f"Creating user in Firebase Auth: {email}")
            user = pyre_auth.create_user_with_email_and_password(email, password)
            uid = user['localId']
            logging.info(f"User created in Firebase Auth with UID: {uid}")
            
            # Prepare data for Firebase Realtime Database
            user_data = {
                "empresa": {
                    "nombre_empresa": nombre_empresa,
                    "nit": nit,
                    "numero_contacto": numero_contacto,
                    "direccion": direccion
                },
                "representante_legal": {
                    "nombre": nombre_representante,
                    "numero_identificacion": numero_identificacion,
                    "email": email # Store email here as well for easy retrieval
                }
            }

            # Upload logo to Cloudinary if provided
            if logo_empresa and logo_empresa.filename != '':
                logging.info("Logo file detected, attempting Cloudinary upload.")
                try:
                    result = cloudinary.uploader.upload(logo_empresa)
                    user_data["empresa"]["logo_url"] = result['secure_url']
                    logging.info(f"Cloudinary upload successful: {result['secure_url']}")
                except Exception as cloudinary_e:
                    logging.error(f"Cloudinary upload failed: {cloudinary_e}")
                    flash(f"Error al subir el logo: {str(cloudinary_e)}", "error")
                    # Consider if you want to stop registration or proceed without logo
                    # For now, we'll proceed, but the logo_url won't be saved.

            # Save data to Firebase Realtime Database
            logging.info(f"Saving user data to Firebase Realtime Database for UID: {uid}")
            db.reference(f'usuarios/{uid}').set(user_data)
            logging.info(f"User data saved successfully for UID: {uid}. Data: {user_data}")

            flash("Empresa registrada correctamente. Ahora inicia sesión.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            logging.error(f"Error during registration process for {email}: {e}", exc_info=True) # exc_info=True to log traceback
            if "EMAIL_EXISTS" in str(e):
                flash("Este correo electrónico ya está registrado.", "error")
            else:
                flash(f"Error al crear usuario: {str(e)}", "error")
    return render_template("register.html")

@app.route('/inventario')
def inventario():
    """ Página de inventario """
    if 'user' not in session:
        return redirect(url_for("login"))
    uid = session['user']['uid']
    
    # Retrieve company name from 'empresa' node for display
    empresa_data = db.reference(f'usuarios/{uid}/empresa').get()
    nombre_empresa = empresa_data.get('nombre_empresa', 'Empresa') if empresa_data else 'Empresa'
    
    productos = db.reference(f'usuarios/{uid}/productos').get() or {}
    logging.info(f"Inventario loaded for UID: {uid}")
    return render_template("inventario.html", perfil=nombre_empresa, productos=productos, empresa_info=empresa_data)


@app.route('/agregar_producto', methods=["POST"])
def agregar_producto():
    if 'user' not in session:
        return redirect(url_for("login"))
    uid = session['user']['uid']

    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    cantidad = request.form.get('cantidad')
    precio = request.form.get('precio')
    
    if nombre and cantidad and cantidad.isdigit() and precio and precio.replace('.', '', 1).isdigit():
        producto_data = {
            "nombre": nombre,
            "descripcion": descripcion,
            "cantidad": int(cantidad),
            "precio": float(precio)
        }
        
        # --- INICIO MODIFICACIÓN PARA MULTIPLES IMAGENES ---
        uploaded_image_urls = []
        # 'imagen' es el nombre del input file en el HTML, y 'multiple' permite una lista de archivos
        files = request.files.getlist('imagen') 
        
        for file in files:
            if file and file.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(file)
                    uploaded_image_urls.append(upload_result['secure_url'])
                    logging.info(f"Image uploaded to Cloudinary: {upload_result['secure_url']}")
                except Exception as e:
                    logging.error(f"Error uploading image to Cloudinary: {e}")
                    flash(f"Error al subir una imagen: {str(e)}", "error")
        
        # Almacena la lista de URLs en Firebase bajo la clave 'imagenes'
        # Si no hay imágenes subidas, la lista estará vacía, lo cual es manejado por el frontend
        if uploaded_image_urls: # Solo guarda la clave si hay imágenes
            producto_data["imagenes"] = uploaded_image_urls
        # --- FIN MODIFICACIÓN PARA MULTIPLES IMAGENES ---
        
        try:
            db.reference(f'usuarios/{uid}/productos').push(producto_data)
            logging.info(f"Product '{nombre}' added for UID: {uid}")
            flash("Producto agregado correctamente.", "success")
        except Exception as e:
            logging.error(f"Error adding product to Firebase for UID {uid}: {e}")
            flash(f"Error al agregar producto: {str(e)}", "error")
    else:
        logging.warning(f"Invalid product data for UID: {uid}. Data: {request.form}")
        flash("Por favor ingresa datos válidos.", "error")

    return redirect(url_for("inventario"))

@app.route('/eliminar_producto/<producto_id>', methods=["POST"])
def eliminar_producto(producto_id):
    """ Elimina producto del inventario """
    if 'user' not in session:
        return redirect(url_for("login"))
    uid = session['user']['uid']
    try:
        # Opcional: Si las imágenes antiguas necesitan ser eliminadas de Cloudinary,
        # primero tendrías que recuperar las URLs del producto antes de eliminarlo de Firebase
        # y luego usar cloudinary.uploader.destroy()
        
        db.reference(f'usuarios/{uid}/productos/{producto_id}').delete()
        logging.info(f"Product '{producto_id}' deleted for UID: {uid}.")
        flash("Producto eliminado correctamente.", "success")
    except Exception as e:
        logging.error(f"Error deleting product '{producto_id}' for UID: {uid}: {e}")
        flash(f"Error al eliminar producto: {str(e)}", "error")
    return redirect(url_for("inventario"))

@app.route('/editar_producto/<producto_id>', methods=["GET", "POST"])
def editar_producto(producto_id):
    if 'user' not in session:
        return redirect(url_for("login"))
    
    uid = session['user']['uid']
    producto_ref = db.reference(f'usuarios/{uid}/productos/{producto_id}')
    
    # --- INICIO CORRECCIÓN PARA AttributeError: 'dict' object has no attribute 'val' ---
    producto_data_snapshot = producto_ref.get()
    # Verifica si producto_data_snapshot es un objeto que tiene el método .val() (como podría ser un DataSnapshot de Pyrebase)
    # o si ya es un diccionario (como lo es con Firebase Admin SDK)
    if hasattr(producto_data_snapshot, 'val'):
        producto = producto_data_snapshot.val()
    else:
        producto = producto_data_snapshot # Ya es un diccionario
    # --- FIN CORRECCIÓN ---

    if not producto:
        flash("Producto no encontrado.", "error")
        return redirect(url_for("inventario"))

    if request.method == 'POST':
        # Recopilar los datos del formulario (excepto las imágenes por ahora)
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        cantidad = request.form.get('cantidad')
        precio = request.form.get('precio')

        if nombre and cantidad and cantidad.isdigit() and precio and precio.replace('.', '', 1).isdigit():
            data_update = {
                "nombre": nombre,
                "descripcion": descripcion,
                "cantidad": int(cantidad),
                "precio": float(precio)
            }

            # --- INICIO MODIFICACIÓN PARA MULTIPLES IMAGENES EN EDICIÓN ---
            files = request.files.getlist('imagen') # Obtener todos los archivos subidos
            new_image_urls = []
            
            has_new_files = False
            for file in files:
                if file and file.filename != '':
                    has_new_files = True
                    try:
                        upload_result = cloudinary.uploader.upload(file)
                        new_image_urls.append(upload_result['secure_url'])
                        logging.info(f"New image uploaded for product '{producto_id}': {upload_result['secure_url']}")
                    except Exception as e:
                        logging.error(f"Error uploading new image for product '{producto_id}': {e}")
                        flash(f"Error al subir una de las nuevas imágenes: {str(e)}", "error")
            
            if has_new_files:
                # Si se subieron nuevas imágenes, reemplaza todas las imágenes existentes con las nuevas
                data_update["imagenes"] = new_image_urls
                # Si el producto tenía una sola 'imagen_url' antigua, la eliminamos para evitar duplicidades/conflictos
                if "imagen_url" in producto and producto["imagen_url"]:
                    data_update["imagen_url"] = None # Establece a None para que se elimine en Firebase
                    logging.info(f"Marked old 'imagen_url' for removal for product '{producto_id}' as new images were uploaded.")
            # Si no se suben nuevos archivos, no modificamos las claves 'imagenes' o 'imagen_url' en data_update.
            # Esto asegura que las imágenes existentes en Firebase (ya sea 'imagen_url' o 'imagenes') se conserven.
            # --- FIN MODIFICACIÓN PARA MULTIPLES IMAGENES EN EDICIÓN ---

            try:
                producto_ref.update(data_update)
                logging.info(f"Product '{producto_id}' updated for UID: {uid}. Data: {data_update}")
                flash("Producto actualizado correctamente.", "success")
                return redirect(url_for("inventario"))
            except Exception as e:
                logging.error(f"Error updating product '{producto_id}' in Firebase for UID {uid}: {e}")
                flash(f"Error al actualizar producto: {str(e)}", "error")
        else:
            logging.warning(f"Invalid data for product update '{producto_id}' for UID: {uid}. Data: {request.form}")
            flash("Datos inválidos.", "error")
    
    # Para la solicitud GET, o si POST falla
    return render_template("editar_producto.html", producto=producto, producto_id=producto_id)

# --- NUEVA RUTA PARA ACTUALIZAR LA CANTIDAD DEL PRODUCTO VÍA AJAX ---
@app.route('/actualizar_cantidad_producto/<producto_id>', methods=['POST'])
def actualizar_cantidad_producto(producto_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Necesitas iniciar sesión.'}), 401 # Unauthorized

    uid = session['user']['uid']
    producto_ref = db.reference(f'usuarios/{uid}/productos/{producto_id}')

    try:
        data = request.get_json()
        new_quantity = int(data.get('cantidad'))

        if new_quantity < 0:
            return jsonify({'success': False, 'message': 'La cantidad no puede ser negativa.'}), 400

        # Optional: Get current product data to ensure it exists before updating
        current_product = producto_ref.get()
        if not current_product:
            return jsonify({'success': False, 'message': 'Producto no encontrado.'}), 404

        producto_ref.update({'cantidad': new_quantity})
        logging.info(f"Cantidad del producto '{producto_id}' actualizada a {new_quantity} para UID: {uid}.")
        return jsonify({'success': True, 'message': 'Cantidad actualizada correctamente.'})

    except ValueError:
        return jsonify({'success': False, 'message': 'Cantidad inválida. Debe ser un número entero.'}), 400
    except Exception as e:
        logging.error(f"Error al actualizar cantidad del producto '{producto_id}' para UID {uid}: {e}")
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/logout')
def logout():
    """ Cierra la sesión """
    session.clear()
    logging.info("User logged out.")
    return redirect(url_for("home"))

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)