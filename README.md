A continuacion se demuestran todos los contenidos, capturas, codigo y usos correspondientes a la realizacion de la Entrega Final de Proyecto del curso de Programacion Basica de Computadores

El proyecto realizado con los lenguajes de programacion Python ( Codigo Principal ) y HTML ( Vistas de pagina web ) se realizo con el proprosito de diseñar una base de datos 
( Realizada con ayuda de Firebase Realtime Database ), donde los usuarios tras registrarse e iniciar sesion, fueran capaces de agregar productos a sus bases de datos, los cuales 
cuenten con nombre, descripcion, cantidad, precio y finalmente, un carrusel desde donde se desplieguen varias imagenes del producto, subidas por el mismo usuario. A continuacion se detallara
el cumplimiento de todos estos propositos originales: ( Para mas informacion leer el documento de presentacion del proyecto )

Registro y Inicio de Sesion del Usuario 
Para el registro y autenticacion de usuarios dentro de la base de datos, se realizo con ayuda de Firebase y mas especificamente desde su herramienta authentication, desde donde al asociar un correo
y un contraseña de minimo 6 caracteres, se generaba un nuevo perfil para cada usuario con un UID unico alojado en Realtime Database, desde donde posteriormente se alojaran todos los demas datos e 
informacion asociados a dicho perfil.

Pantalla de Inicio de la Pagina Web
<img width="1862" height="923" alt="image" src="https://github.com/user-attachments/assets/0112fc3d-8f2f-4602-b5a8-61cc73417a90" />

Una vez la aplicacion se ejecuta por primera vez se muestra un menu principal desde donde podemos escoger de dos opcioness distintas: "Registrase" e "Iniciar Sesion", los cuales al ser pulsados nos
redirigen a sus correspondientes nuevos menus

Pantalla del menu Registrarse
<img width="1845" height="927" alt="image" src="https://github.com/user-attachments/assets/85bfdd50-c3ad-4092-af02-04ec2181b397" />
Una vez en el menu registrarse, tal y como su nombre lo indica se permitira crear un nuevo perfil asociado a una empresa, con el proposito de que pueda empezar a incluir sus productos dentro de ella.
Al entrar en la pagina se nos muestra un formulario desde donde debemos rellenar diferentes datos y demas informacion de nuestra empresa tales como: Nombre de la empresa, NIT, Logo, Numero de contacto y
Direccion. Ademas de un apartado correspondiente al Representante Legal donde se solicitara la siguiente informacion: Nombre del Representante Legal, Número de Identificación, Correo Electrónico y Contraseña;
siendo estos dos utimos las credenciales utilizadas para inciar sesion en la siguiente pantalla al oprimir el boton "Confirmar Registro"


Pantalla del menu Iniciar Sesion
<img width="1845" height="923" alt="image" src="https://github.com/user-attachments/assets/ec7e4f82-141f-4d4c-b621-3a9be24c8f57" />

Una vez hecho el registro, se oprimira el boton "Confirmar Registro" el cual nos redirigira hacia el menu de Iniciar Sesion, una vez aqui con ayuda del correo electronico y contraseña suministrada anteriormente
se podra acceder finalmente al menu de inventario de la pagina web. 

Pantalla del menu Inventario
<img width="1847" height="928" alt="image" src="https://github.com/user-attachments/assets/0c6dbb22-8999-408d-94fa-74ae4965d2b6" />

Una vez accedido al menu de inventario de despliegara una serie de ventanas desde donde en la parte superior de la pagina, se podra consultar nuevamente la informacion y demas suministrados en el proceso de 
registro, un boton con la capacidad de editar alguno de ellos y finalmente la opcion de agregar un nuevo producto, los cuales se enseñaran en la parte inferior de la pagina

Pantalla del Boton Agregar Producto
<img width="1837" height="925" alt="image" src="https://github.com/user-attachments/assets/1ab87c23-887c-422a-aeb2-0f84c6820e50" />

Pantalla del Boton Editar Informacion de la Empresa
<img width="1847" height="920" alt="image" src="https://github.com/user-attachments/assets/579ec449-14e5-4230-a116-54fdb5e4f2a3" />

El funcionamiento de estos dos botones es bastantae similar, puesto que es abrira un formulario desde donde se podran ingresar los diferentes datos para cada uno de ellos, ya sea que se desee editar la 
informacion de la empresa, o por otra parte, que se desee agregar un nuevo producto a la base de datos. Sea cual sea el caso, se debera rellenar los campos con la informacion correspondiente, y al final,
se genera la opcion de ingresar una nueva imagen para el logo de la empresa ( Una sola imagen ) o en el caso de los productos, la posbilidad de agregar 1 o mas imagenes con el proposito de hacer funcionar
el carrusel de imagenes dispuesto dentro del menu inventario.

Cabe resaltar que con el prososito de facilitar el proceso, sin la necesidad de oprimir el Boton Editar Producto, cuyo funcionamiento es exactamente igual al Boton Agregar Producto, se podra editar la cantidad
de elementos de determinado producto en cualquier momento desde el menu de inventario, tal y como se muestra en la siguiente imagen
<img width="1132" height="332" alt="image" src="https://github.com/user-attachments/assets/988815a2-dc71-478a-abba-e6e0e039b67a" />

Finalmente una vez se termine de consultar, agregar y/o editar los productos se cuenta con un boton final llamado "Cerrar Sesion" desde donde al orpimirlo finalizaremos la sesion actual, y exigiremos que la
proxima vez que se consulte la pagina se deba realizar el proceso de autenticacion nuevamente, redirigiendonos al menu de Pantalla de Inicio de la pagina web.
<img width="247" height="105" alt="image" src="https://github.com/user-attachments/assets/36e1c5c9-efc7-4e30-a976-2f20749b04bd" />






Finalmente, y como comentario adicional, debido a la herramienta de Host usada para la pagina web, en este caso Render, al ser Hosteada con el plan gratis en caso de que la pagina no detecte actividad por
mas de 15 minutos, render pondra en un estado de "Hibernacion" la pagina, en donde se apagara por unos breves instantes, y al ser consultada nuvamente, se reiniciara sin haber cerrado la sesion trabajada
anteriormente.

Reinicio de Host por Inactividad ( Mas de 12 horas )
<img width="1857" height="936" alt="image" src="https://github.com/user-attachments/assets/889efb01-bc54-41c0-bd5f-b137b0d58c64" />
