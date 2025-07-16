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

# Configurar Cloudinary con tus credenciales
cloudinary.config(
    cloud_name = 'df03k7eoe', # Reemplaza con tu Cloud Name
    api_key = '114675893934974', # Reemplaza con tu API Key
    api_secret = 'a9pcGnEBjfM0-neAPR46t2KY5QQ' # Reemplaza con tu API Secret
)

app = Flask(__name__)
app.secret_key = '123456'  # Cambia esta clave en producción a algo más seguro

# -------------------- CONFIGURACIÓN FIREBASE --------------------
# Asegúrate de que stockmarket-testbase.json está en el mismo directorio o proporciona la ruta completa
# Es mejor usar variables de entorno para las credenciales en producción.
try:
    cred = credentials.Certificate("stockmarket-testbase.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://stockmarket-e92e2-default-rtdb.firebaseio.com/" # Reemplaza con tu Database URL
        })
    logging.info("Firebase Admin SDK inicializado correctamente.")
except Exception as e:
    logging.error(f"Error al inicializar Firebase Admin SDK: {e}")
    # Considerar una salida más robusta o un mensaje de error al usuario
    # sys.exit(1) # Podría ser útil en un script de inicio

firebase_config = {
    "apiKey": "AIzaSyDWPdr2ADEeZYDfk58TgFLfAr5XfqRY_Xo", # Reemplaza
    "authDomain": "stockmarket-e92e2.firebaseapp.com", # Reemplaza
    "databaseURL": "https://stockmarket-e92e2-default-rtdb.firebaseio.com/", # Reemplaza
    "projectId": "stockmarket-e92e2", # Reemplaza
    "storageBucket": "stockmarket-e92e2.appspot.com", # Reemplaza
    "messagingSenderId": "156560897736", # Reemplaza
    "appId": "1:156560897736:web:7ac36bae494b4b8bc1dc7d", # Reemplaza
    "measurementId": "G-2RCVXNKBBZN" # Reemplaza
}

try:
    firebase = pyrebase.initialize_app(firebase_config)
    pyre_auth = firebase.auth()
    logging.info("Pyrebase inicializado correctamente.")
except Exception as e:
    logging.error(f"Error al inicializar Pyrebase: {e}")
    # Considerar una salida más robusta o un mensaje de error al usuario

db = db

# -------------------- RUTAS --------------------

@app.route('/')
def home():
    """Ruta de inicio para login y registro."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = pyre_auth.sign_in_with_email_and_password(email, password)
            session['user'] = user['localId'] # Guardar el UID en la sesión
            flash("Inicio de sesión exitoso.", "success")
            logging.info(f"Usuario {email} ha iniciado sesión.")
            return redirect(url_for('inventario'))
        except Exception as e:
            error_message = "Credenciales inválidas."
            if "EMAIL_NOT_FOUND" in str(e):
                error_message = "El correo electrónico no está registrado."
            elif "INVALID_PASSWORD" in str(e):
                error_message = "Contraseña incorrecta."
            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in str(e):
                error_message = "Demasiados intentos fallidos. Inténtalo de nuevo más tarde."
            flash(error_message, "error")
            logging.warning(f"Fallo de inicio de sesión para {email}: {error_message}")
            return render_template('login.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        nombre_empresa = request.form.get('nombre_empresa')
        nit = request.form.get('nit')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono') # Nuevo campo
        nombre_representante = request.form.get('nombre_representante')
        numero_identificacion = request.form.get('numero_identificacion')
        logo_empresa = request.files.get('logo_empresa') # Archivo subido

        if not all([email, password, nombre_empresa, nit, direccion, nombre_representante, numero_identificacion]):
            flash("Todos los campos obligatorios deben ser rellenados.", "error")
            return render_template('register.html')

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template('register.html')

        try:
            # Crear usuario en Firebase Authentication
            user = pyre_auth.create_user_with_email_and_password(email, password)
            uid = user['localId']
            logging.info(f"Usuario creado en Auth: {email}, UID: {uid}")

            logo_url = None
            if logo_empresa and logo_empresa.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(logo_empresa)
                    logo_url = upload_result['secure_url']
                    logging.info(f"Logo subido para {email}: {logo_url}")
                except Exception as e:
                    flash("Error al subir el logo de la empresa. Por favor, inténtalo de nuevo.", "error")
                    logging.error(f"Error al subir el logo para {email}: {e}")
                    # Considerar revertir la creación del usuario si la subida del logo es crítica
                    admin_auth.delete_user(uid) # Eliminar usuario si no se puede subir el logo
                    return render_template('register.html')

            # Guardar datos adicionales en Realtime Database
            db.reference(f'usuarios/{uid}/perfil').set({
                "nombre_empresa": nombre_empresa,
                "nit": nit,
                "direccion": direccion,
                "telefono": telefono,
                "nombre_representante": nombre_representante,
                "numero_identificacion": numero_identificacion,
                "logo_url": logo_url # Guardar la URL del logo
            })
            logging.info(f"Perfil de usuario guardado en DB para UID: {uid}")

            session['user'] = uid # Iniciar sesión automáticamente
            flash("Registro exitoso. ¡Bienvenido a StockMarket!", "success")
            return redirect(url_for('inventario'))

        except Exception as e:
            error_message = "Error al registrar el usuario."
            if "EMAIL_EXISTS" in str(e):
                error_message = "El correo electrónico ya está registrado."
            flash(error_message, "error")
            logging.error(f"Error durante el registro de {email}: {e}")
            return render_template('register.html')
    return render_template('register.html')


@app.route('/inventario')
def inventario():
    if 'user' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "error")
        return redirect(url_for('login'))

    uid = session['user'] # El UID se guarda directamente en session['user']
    
    # Obtener datos del perfil de la empresa
    perfil_data = db.reference(f'usuarios/{uid}/perfil').get()
    if not perfil_data:
        perfil_data = {} # Asegura que perfil_data sea un diccionario si no hay datos

    productos = db.reference(f'usuarios/{uid}/productos').get()
    if not productos:
        productos = {} # Asegura que productos sea un diccionario si no hay productos

    # Convertir el diccionario de productos a una lista de diccionarios para facilitar la iteración
    # y añadir el id del producto a cada uno. Además, manejar imagen_url a imagen_urls.
    productos_list = {} # Cambiamos a diccionario para mantener el ID como clave
    for prod_id, prod_data in productos.items():
        prod_data['id'] = prod_id
        # Si imagen_url existe, convertirla a una lista de imagen_urls
        if 'imagen_url' in prod_data and isinstance(prod_data['imagen_url'], str):
            prod_data['imagen_urls'] = [prod_data['imagen_url']]
            del prod_data['imagen_url'] # Eliminar el campo antiguo
        elif 'imagen_url' in prod_data and isinstance(prod_data['imagen_url'], list):
            prod_data['imagen_urls'] = prod_data['imagen_url']
        else:
            prod_data['imagen_urls'] = [] # Asegura que siempre sea una lista

        productos_list[prod_id] = prod_data # Guardar como diccionario con ID como clave


    # No es necesario ordenar si se usa un diccionario con IDs, el orden lo da Firebase.
    # Si se necesita un orden específico, se convertiría a lista y se ordenaría.

    return render_template('inventario.html', 
                           productos=productos_list,
                           perfil_data=perfil_data) # Pasar los datos del perfil

@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    if 'user' not in session:
        flash("Debes iniciar sesión para agregar productos.", "error")
        return redirect(url_for('login'))

    uid = session['user']
    
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    cantidad = request.form.get('cantidad')
    precio = request.form.get('precio')
    imagenes = request.files.getlist('imagen') # Obtener una lista de archivos

    if not all([nombre, cantidad, precio]):
        flash("Nombre, cantidad y precio son obligatorios.", "error")
        return redirect(url_for('inventario'))

    try:
        cantidad = int(cantidad)
        precio = float(precio)
        if cantidad < 0 or precio < 0:
            flash("Cantidad y precio deben ser valores positivos.", "error")
            return redirect(url_for('inventario'))
    except ValueError:
        flash("Cantidad o precio inválidos. Deben ser números.", "error")
        return redirect(url_for('inventario'))

    imagen_urls = []
    if imagenes:
        for imagen in imagenes:
            if imagen and imagen.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(imagen)
                    imagen_urls.append(upload_result['secure_url'])
                except Exception as e:
                    logging.error(f"Error al subir imagen a Cloudinary: {e}")
                    flash(f"Error al subir una imagen: {e}", "error")
                    # No abortar si una imagen falla, pero notificar.
                    # Podrías decidir revertir todo si todas las imágenes fallan.

    try:
        new_product_ref = db.reference(f'usuarios/{uid}/productos').push()
        new_product_ref.set({
            "nombre": nombre,
            "descripcion": descripcion,
            "cantidad": cantidad,
            "precio": precio,
            "imagen_urls": imagen_urls, # Guardar como lista de URLs
            "fecha_creacion": datetime.now().isoformat()
        })
        flash("Producto agregado correctamente.", "success")
    except Exception as e:
        logging.error(f"Error al agregar producto a Firebase: {e}")
        flash(f"Error al agregar el producto: {e}", "error")
    
    return redirect(url_for('inventario'))


@app.route('/eliminar_producto/<producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    if 'user' not in session:
        flash("Debes iniciar sesión para eliminar productos.", "error")
        return redirect(url_for('login'))

    uid = session['user']
    try:
        db.reference(f'usuarios/{uid}/productos/{producto_id').delete()
        flash("Producto eliminado correctamente.", "success")
    except Exception as e:
        flash(f"Error al eliminar el producto: {e}", "error")
    return redirect(url_for('inventario'))

@app.route('/editar_producto/<producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    if 'user' not in session:
        flash("Debes iniciar sesión para editar productos.", "error")
        return redirect(url_for('login'))

    uid = session['user']
    producto_ref = db.reference(f'usuarios/{uid}/productos/{producto_id}')
    producto = producto_ref.get()

    if not producto:
        flash("Producto no encontrado.", "error")
        return redirect(url_for('inventario'))

    # Asegurarse de que imagen_url sea una lista para la plantilla si solo existe una
    if 'imagen_url' in producto and isinstance(producto['imagen_url'], str):
        producto['imagen_urls'] = [producto['imagen_url']]
        del producto['imagen_url']
    elif 'imagen_url' not in producto:
        producto['imagen_urls'] = [] # Asegurar que exista siempre


    if request.method == "POST":
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        cantidad = request.form.get('cantidad')
        precio = request.form.get('precio')
        nuevas_imagenes = request.files.getlist('imagen') # Obtener lista de nuevos archivos

        if nombre and cantidad.isdigit() and precio.replace('.', '', 1).isdigit():
            data_update = {
                "nombre": nombre,
                "descripcion": descripcion,
                "cantidad": int(cantidad),
                "precio": float(precio)
            }

            current_image_urls = producto.get('imagen_urls', []) # Obtener las URLs actuales

            uploaded_image_urls = []
            for imagen in nuevas_imagenes:
                if imagen and imagen.filename != "":
                    try:
                        result = cloudinary.uploader.upload(imagen)
                        uploaded_image_urls.append(result['secure_url'])
                    except Exception as e:
                        logging.error(f"Error al subir nueva imagen para producto {producto_id}: {e}")
                        flash(f"Error al subir una de las nuevas imágenes: {e}", "error")
                        # No detener la operación, pero notificar.

            if uploaded_image_urls:
                data_update["imagen_urls"] = uploaded_image_urls # Reemplazar con las nuevas imágenes
            else:
                data_update["imagen_urls"] = current_image_urls # Mantener las existentes si no se subieron nuevas


            try:
                producto_ref.update(data_update)
                flash("Producto actualizado correctamente.", "success")
                return redirect(url_for("inventario"))
            except Exception as e:
                logging.error(f"Error al actualizar el producto en Firebase: {e}")
                flash(f"Error al actualizar el producto: {e}", "error")
                return render_template("editar_producto.html", producto=producto, producto_id=producto_id)
        else:
            flash("Datos inválidos.", "error")
            return render_template("editar_producto.html", producto=producto, producto_id=producto_id)

    # GET: solo renderiza el formulario con los datos existentes
    return render_template("editar_producto.html", producto=producto, producto_id=producto_id)

@app.route('/actualizar_cantidad/<producto_id>', methods=['POST'])
def actualizar_cantidad(producto_id):
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'No autorizado.'}), 401

    uid = session['user']
    producto_ref = db.reference(f'usuarios/{uid}/productos/{producto_id}')

    try:
        data = request.get_json()
        new_quantity = int(data.get('cantidad'))

        if new_quantity < 0:
            return jsonify({'success': False, 'message': 'La cantidad no puede ser negativa.'}), 400

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

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():
    """
    Maneja la edición de los datos del perfil de la empresa (nombre, NIT, dirección, logo, etc.).
    """
    if 'user' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "error")
        return redirect(url_for('login'))

    uid = session['user']
    perfil_ref = db.reference(f'usuarios/{uid}/perfil')

    if request.method == 'POST':
        nombre_empresa = request.form.get('nombre_empresa')
        nit = request.form.get('nit')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')

        nombre_representante = request.form.get('nombre_representante')
        numero_identificacion = request.form.get('numero_identificacion')
        
        logo_empresa = request.files.get('logo_empresa')

        # Obtener los datos actuales para mantenerlos en caso de error o para conservar el logo
        current_perfil_data = perfil_ref.get() or {} 
        
        # Validaciones de campos obligatorios
        if not all([nombre_empresa, nit, direccion, nombre_representante, numero_identificacion]):
            flash("Todos los campos obligatorios de la empresa y representante deben ser rellenados.", "error")
            # Recargar perfil_data, pero con los datos POST que ya se enviaron para no perderlos
            perfil_data_to_render = current_perfil_data.copy()
            perfil_data_to_render.update({
                'nombre_empresa': nombre_empresa, 'nit': nit, 'direccion': direccion, 'telefono': telefono,
                'nombre_representante': nombre_representante, 'numero_identificacion': numero_identificacion
            })
            return render_template('editar_perfil.html', perfil_data=perfil_data_to_render)

        data_update = {
            "nombre_empresa": nombre_empresa,
            "nit": nit,
            "direccion": direccion,
            "telefono": telefono,
            "nombre_representante": nombre_representante,
            "numero_identificacion": numero_identificacion
        }

        # Manejo de la subida del logo
        if logo_empresa and logo_empresa.filename != '':
            try:
                # Subir la imagen a Cloudinary
                upload_result = cloudinary.uploader.upload(logo_empresa)
                data_update["logo_url"] = upload_result['secure_url']
                logging.info(f"Nuevo logo subido para UID {uid}: {data_update['logo_url']}")
            except Exception as e:
                logging.error(f"Error al subir el logo a Cloudinary para UID {uid}: {e}")
                flash("Error al subir el logo de la empresa. Por favor, inténtalo de nuevo.", "error")
                # Si hay un error al subir la imagen, conservar el logo anterior si existía
                data_update["logo_url"] = current_perfil_data.get('logo_url')
                return render_template('editar_perfil.html', perfil_data={**current_perfil_data, **data_update})
        else:
            # Si no se sube un nuevo logo, mantener el existente
            if 'logo_url' in current_perfil_data:
                data_update["logo_url"] = current_perfil_data['logo_url']
            else:
                data_update["logo_url"] = None # O asegura que no haya campo si no existe

        try:
            perfil_ref.update(data_update)
            flash("Perfil actualizado correctamente.", "success")
            return redirect(url_for('inventario'))
        except Exception as e:
            logging.error(f"Error al actualizar el perfil en Firebase para UID {uid}: {e}")
            flash(f"Error al actualizar el perfil: {e}", "error")
            # En caso de error, volvemos a renderizar el formulario con los datos enviados
            # Esto fusiona los datos actuales con los datos del POST para precargar el formulario
            return render_template('editar_perfil.html', perfil_data={**current_perfil_data, **data_update})

    else: # GET request
        perfil_data = perfil_ref.get()
        if not perfil_data: # Si no hay datos de perfil, inicializar con valores vacíos
            perfil_data = {
                'nombre_empresa': '', 'nit': '', 'direccion': '', 'telefono': '',
                'logo_url': '',
                'nombre_representante': '', 'numero_identificacion': ''
            }
        return render_template('editar_perfil.html', perfil_data=perfil_data)


@app.route('/logout')
def logout():
    """ Cierra la sesión """
    session.clear()
    logging.info("User logged out.")
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("login")) # Redirigir a login, no a home

# -------------------- MAIN --------------------
if __name__ == '__main__':
    # Usar puerto 8000 para Render, o 5000 para desarrollo local si no hay variable de entorno
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 