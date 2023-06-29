"""
GEMPROP - [Ge]stor de [M]ateriales, [Pro]ducción y [P]edidos

Las funciones de la aplicación se organizan en 3 grupos, conforme al patron MVC:
1) Modelo: implementa la gestión de registros (crud) en una base de datos SQLite
2) Vista: soporta la capa visual utilizando tkinter
3) Controlador: invoca a las funciones del modelo según las reglas de negocio de la aplicación
"""

###############################################################################
# Módulos requeridos por la aplicación
###############################################################################
from tkinter import *
from tkinter.font import Font       # Fuentes para labels
from tkinter import ttk             # Objeto TreeView
from tkinter.messagebox import *    # Diálogos en pantalla
from datetime import datetime       # Obtención de fecha y hora actual
from sqlite3 import Error           # Gestión de errores accediendo a la base de datos
import sqlite3                      # Objetos de manejo de la base de datos
import os                           # Método path
import re                           # Expresiones regulares para campos numéricos
import json                         # Materiales asociados a un producto
import sys                          # Obtener nombre de la base de datos por la línea de comandos
import platform                     # Identifica al sistema operativo usado
from PIL import ImageTk, Image      # Imagen de la bandera mostrada en la esquina inferior-derecha

###############################################################################
# Variables globales de la aplicación
###############################################################################

nombre_base_de_datos = "gemprop.db"
nombre_sistema_operativo = ""

# Objeto principal tkinter
ventana_principal = Tk()
ventana_principal.winfo_toplevel().title("Gestor de Materiales, Productos y Pedidos")
ventana_principal.geometry("950x550")

# Edición de campos - Materiales
diccionario_materiales = {
    "id": IntVar(),
    "descripcion": StringVar(),
    "stock_actual": IntVar(),
    "stock_reposicion": IntVar(),
    "demora_reposicion": IntVar()
}

# Edición de campos - Productos
diccionario_productos = {
    "id": IntVar(),
    "descripcion": StringVar()
}

# Variables para definir formatos visuales específicos a cada sistema operativo usado
fuente_titulo_1 = None
fuente_titulo_2 = None
fuente_normal = None
ancho_boton_ayuda = 0
ancho_boton_normal = 0
ancho_boton_xl = 0
ancho_boton_xxl = 0

# Path
DIRECTORIO_APLICACION = os.path.dirname((os.path.abspath(__file__)))
DIRECTORIO_IMAGENES = os.path.join(DIRECTORIO_APLICACION, "img")

# Objetos TreeView
treeview_materiales = None
treeview_productos = None
treeview_materiales_por_producto = None

# Objetos Combobox
combobox_materiales = None
combobox_productos = None

# Objetos Entry
entry_cantidad_de_material = IntVar()

# Base de datos
conexion_bd = None
cursor_bd = None

###############################################################################
# 1) MODELO
###############################################################################

def aplicar_ajustas_por_sistema_operativo(nombre_sistema_operativo):

    global fuente_titulo_1, fuente_titulo_2, fuente_normal
    global ancho_boton_normal, ancho_boton_xl, ancho_boton_xxl, ancho_boton_ayuda

    # Ajustar el tamaño de las fuentes según el sistema operativo usado
    tamaños_fuentes = (20, 12, 10)          # Tamaños usados en Windows y Linux
    ancho_boton_normal = 8
    ancho_boton_xl = 10
    ancho_boton_xxl = 12
    ancho_boton_ayuda = 2
    if nombre_sistema_operativo == "MacOS": # Tamaños usados en MacOS
        tamaños_fuentes = (24, 16, 12)
        ancho_boton_normal = 4
        ancho_boton_xl = 6
        ancho_boton_xxl = 10
        ancho_boton_ayuda = 1
    fuente_titulo_1 = Font(font=('Arial', tamaños_fuentes[0]), weight='bold', underline=1)
    fuente_titulo_2 = Font(font=('Arial', tamaños_fuentes[1]), weight='bold')
    fuente_normal = Font(font=('Arial', tamaños_fuentes[2]))

def registrar_evento(texto):
    # Muestra un mensaje de información en la consola, anteponiendo la fecha y hora del mismo
    fecha_actual = datetime.now()
    fecha_formateada = ("{}/{:02}/{:02} {}:{:02}:{:02}".format(fecha_actual.year, fecha_actual.month, fecha_actual.day, fecha_actual.hour, fecha_actual.minute, fecha_actual.second))
    print(f"[{fecha_formateada}] {texto}")

def mostrar_mensaje(argumentos):
    # Muestra un alerta con el título y mensaje recibidos
    # Si argumentos tiene 1 solo elemento, se lo usa como mensaje a mostrar
    # Si argumentos tiene 2 (o mas) elementos, el primero será el título, y el segundo será el mensaje a mostrar
    if type(argumentos) == str:
        titulo = ""
        mensaje = argumentos
    elif len(argumentos) == 1:
        titulo = ""
        mensaje = argumentos[0]
    else:
        titulo = argumentos[0]
        mensaje = argumentos[1]
        
    showinfo(title=titulo, message=mensaje)

def abrir_base_de_datos(nombre_base_de_datos):
    try:
        conexion_bd = sqlite3.connect(nombre_base_de_datos)
        registrar_evento(f"Se abrió la base de datos [{nombre_base_de_datos}]")
        return conexion_bd
    except sqlite3.Error as err:
        registrar_evento(f"No se puede abrir la base de datos [{nombre_base_de_datos}]")
        ventana_principal.quit()

def crear_tabla_de_materiales(conexion_bd):
    # Crea la tabla de materiales. Si esta ya existe en la base de datos, informa que fue encontrada.
    if ejecutar_sentencia_sql(conexion_bd, "CREATE TABLE materiales (id integer PRIMARY KEY, descripcion text, stock_actual integer, stock_reposicion integer, demora_reposicion integer)") is None:
        registrar_evento("La tabla 'materiales' ya existe en la base de datos")
    else:
        registrar_evento("La tabla 'materiales' fue creada satisfactoriamente en la base de datos")

def crear_tabla_de_productos(conexion_bd):
    # Crea la tabla de productos. Si esta ya existe en la base de datos, informa que fue encontrada.
    if ejecutar_sentencia_sql(conexion_bd, "CREATE TABLE productos (id integer PRIMARY KEY, descripcion text)") is None:
        registrar_evento("La tabla 'productos' ya existe en la base de datos")
    else:
        registrar_evento("La tabla 'productos' fue creada satisfactoriamente en la base de datos")

def crear_tabla_de_materiales_por_producto(conexion_bd):
    # Crea la tabla de materiales asociados a un producto. Si esta ya existe en la base de datos, informa que fue encontrada.
    if ejecutar_sentencia_sql(conexion_bd, "CREATE TABLE materiales_por_producto (id_material integer, id_producto integer, cantidad_de_unidades integer)") is None:
        registrar_evento("La tabla 'materiales_por_producto' ya existe en la base de datos")
    else:
        registrar_evento("La tabla 'materiales_por_producto' fue creada satisfactoriamente en la base de datos")

def materiales_insertar_registro_material(conexion_bd):

    sql = "INSERT INTO materiales(descripcion, stock_actual, stock_reposicion, demora_reposicion) VALUES (?, ?, ?, ?)"
    
    # Se convierte el diccionario de materiales a una tupla
    datos_material = (diccionario_materiales["descripcion"].get(),
                        diccionario_materiales["stock_actual"].get(),
                        diccionario_materiales["stock_reposicion"].get(),
                        diccionario_materiales["demora_reposicion"].get()
                        )
    if ejecutar_sentencia_sql(conexion_bd, sql, datos_material) is None:
        return False
    
    return True

def materiales_actualizar_registro_material(conexion_bd, id_material):
    # Actualiza el registro de la base de datos cuyo ID coincide con el argumento id_material
    datos_material = (diccionario_materiales["descripcion"].get(),
                        diccionario_materiales["stock_actual"].get(),
                        diccionario_materiales["stock_reposicion"].get(),
                        diccionario_materiales["demora_reposicion"].get(),
                        id_material
                        )
    sql = "UPDATE materiales SET descripcion=?, stock_actual=?, stock_reposicion=?, demora_reposicion=? WHERE id=?"
    if ejecutar_sentencia_sql(conexion_bd, sql, datos_material) is None:
        return False
    
    registrar_evento(f"Se actualizó el material con id={str(id_material)}")
    return True


def materiales_buscar_material(conexion_bd, id_material):
    # Obtiene el registro de la base de datos cuyo ID coincide con el argumento id_material
    sql = "SELECT * FROM materiales WHERE id = ?"
    argumentos = (str(id_material),)
    return ejecutar_consulta_sql(conexion_bd, sql, argumentos)


def materiales_recuperar_materiales(conexion_bd):
    # Lee todos los registros de la tabla de materiales
    sql = "SELECT * FROM materiales ORDER BY id ASC"
    return ejecutar_consulta_sql(conexion_bd, sql)


def click_en_material(event):
    global treeview_materiales, diccionario_materiales
    if len(treeview_materiales.selection()) == 0:
        # Se hizo doblel click en un área del treeview donde no hay un material
        return
    material = treeview_materiales.selection()[0]
    diccionario_materiales["id"].set(int(treeview_materiales.item(material)['text']))
    campos = treeview_materiales.item(material)['values']
    diccionario_materiales["descripcion"].set(campos[0])
    diccionario_materiales["stock_actual"].set(int(campos[1]))
    diccionario_materiales["stock_reposicion"].set(int(campos[2]))
    diccionario_materiales["demora_reposicion"].set(int(campos[3]))

def click_en_producto(event):
    global conexion_bd, treeview_productos, diccionario_productos

    if len(treeview_productos.selection()) == 0:
        # Se hizo doble click en un área del treeview donde no hay un producto
        return
    producto = treeview_productos.selection()[0]
    diccionario_productos["id"].set(int(treeview_productos.item(producto)['text']))
    campos = treeview_productos.item(producto)['values']
    diccionario_productos["descripcion"].set(campos[0])

    productos_mostrar_materiales_asociados(conexion_bd)

def productos_insertar_registro_producto(conexion_bd):

    sql = "INSERT INTO productos(descripcion) VALUES (?)"
    datos = (diccionario_productos["descripcion"].get(), )
    return ejecutar_sentencia_sql(conexion_bd, sql, datos)

def productos_recuperar_productos(conexion_bd):
    # Lee todos los registros de la tabla de productos
    sql = "SELECT * FROM productos ORDER BY id ASC"
    registros = ejecutar_consulta_sql(conexion_bd, sql)
    if registros is not None:
        registrar_evento("Se recuperaron todos los registros de la tabla 'productos'")
    
    return registros

def productos_asociar_material_a_producto(conexion_bd, descripcion_material, cantidad_material):
    global treeview_materiales_por_producto

    sql = "SELECT id FROM materiales WHERE descripcion = ?"     # Se obtiene el id único del material seleccionado
    resultado = ejecutar_consulta_sql(conexion_bd, sql, (descripcion_material,))
    if resultado is None:
        return False
    id_material = int(resultado[0][0])

    sql = "INSERT INTO materiales_por_producto(id_material, id_producto, cantidad_de_unidades) VALUES (?, ?, ?)"
    datos = (id_material, diccionario_productos["id"].get(), cantidad_material)
    resultado = ejecutar_sentencia_sql(conexion_bd, sql, datos)
    if resultado is None:
        return False

    # Actualizar el treeview de materiales usados por el producto
    productos_mostrar_materiales_asociados(conexion_bd)

    return True


def productos_desasociar_material_del_producto(conexion_bd, descripcion_material):
    global treeview_materiales_por_producto, diccionario_productos

    sql = "SELECT id FROM materiales WHERE descripcion = ?"     # Se obtiene el id único del material seleccionado
    resultado = ejecutar_consulta_sql(conexion_bd, sql, (descripcion_material,))
    if resultado is None:
        return False
    id_producto = diccionario_productos["id"].get()
    id_material = int(resultado[0][0])

    sql = "DELETE FROM materiales_por_producto WHERE id_material = ? AND id_producto = ?"
    datos = (id_material, id_producto)
    resultado = ejecutar_sentencia_sql(conexion_bd, sql, datos)
    if resultado is None:
        return False

    # Actualizar el treeview de materiales usados por el producto
    productos_mostrar_materiales_asociados(conexion_bd)

    return True


def productos_mostrar_materiales_asociados(conexion_bd):
    global diccionario_productos

    # Obtener la lista actualizada de materiales asociados al producto
    sql = "SELECT materiales.id AS id_material, materiales.descripcion AS descripcion_material, materiales_por_producto.cantidad_de_unidades "\
        "FROM materiales INNER JOIN materiales_por_producto "\
        "ON materiales.id = materiales_por_producto.id_material "\
        "WHERE materiales_por_producto.id_producto = ?"
    datos = (diccionario_productos["id"].get(), )
    registros = ejecutar_consulta_sql(conexion_bd, sql, datos)

    # Actualizar el treeview de materiales por productop
    treeview_materiales_por_producto.delete(*treeview_materiales_por_producto.get_children())   # Se eliminan todos los elementos del treeview antes de refrescarloo
    for registro in registros:
        treeview_materiales_por_producto.insert("", "end", text=str(registro[0]), values=(registro[1], registro[2]))        
    registrar_evento("Se recuperaron todos los registros de la tabla 'materiales_por_producto'")

def pedidos_recuperar_productos(conexion_bd):
    global combobox_productos

    # Recuperar la lista de productos
    tabla_de_productos = productos_recuperar_productos(conexion_bd)
    productos = []
    for registro_de_producto in tabla_de_productos:
        productos.append(registro_de_producto[1])
    combobox_productos['values'] = productos

def pedidos_actualizar_stock():
    if not askyesno("Actualizar Stock", "Confirma la actualización de stock de materiales?"):
        return False
    
    sql = "UPDATE materiales SET stock_actual = (stock_actual + 10) WHERE stock_actual < stock_reposicion"
    materiales_actualizados = ejecutar_sentencia_sql(conexion_bd, sql)
    if materiales_actualizados == 0:
        mostrar_mensaje(["Actualización de Stock", "Proceso finalizado. No se han encontrado materiales que requieran actualización de stock."])
        return True

    # Actualizar el treeview con la lista de materiales del tab Gestión de Materiales
    mostrar_lista_de_materiales(materiales_recuperar_materiales(conexion_bd))

    # Mostrar mensaje de confirmación
    mostrar_mensaje(["Actualización de Stock", f"Se ha actualizado el nivel de stock de {materiales_actualizados} material(es)."])
    return True

def ejecutar_consulta_sql(conexion_bd, consulta_sql, argumentos=None):
    # IMPORTANTE: el argumento 'argumentos' es una tupla (aún si tiene un único argumento) con los valores a reemplazar en la consulta.
    #             Si 'argumentos' == None (o no es provisto), entonces se ejecuta una consulta sin argumentos (ej. SELECT * from <tabla>)

    # Esta función retorna un array conteniendo todos los registros recuperados de la consulta, o None si hubo un error en la consulta

    try:
        cursor = conexion_bd.cursor()
        consulta = None
        if argumentos is None:
            consulta = cursor.execute(consulta_sql)
        else:
            consulta = cursor.execute(consulta_sql, argumentos)
        registros = consulta.fetchall()
        registrar_evento(f"Se ejecutó correctamente la siguiente consulta: {consulta_sql}")
        return registros
    except sqlite3.Error as err:
        registrar_evento(f"Error ejecutando la siguiente consulta SQL: [{consulta_sql}]\nError: [{err.args[0]}]")
    
    return None

def ejecutar_sentencia_sql(conexion_bd, sentencia_sql, argumentos=None):
    # Esta función ejecuta cualquier sentencia SQL recibida que requiera un commit(), por ejemplo un INSERT, UPDATE o DELETE.
    # Si 'argumentos' == None (o no es provisto) se intenta ejecutar solamente la sentencia SQL recibida, cuyos parámetros si los tiene debe enstar hardcodeados (por ejemplo DELETE FROM materiales WHERE id = 5)

    try:
        cursor = conexion_bd.cursor()
        if argumentos is None:
            cursor.execute(sentencia_sql)
        else:
            cursor.execute(sentencia_sql, argumentos)
        conexion_bd.commit()

        filas_afectadas = cursor.rowcount
        registrar_evento(f"Se ejecutó la siguiente sentencia: [{sentencia_sql}].\nSe modificaron {filas_afectadas} fila(s).")
        return filas_afectadas
    except sqlite3.Error as err:
        registrar_evento(f"Error ejecutando la siguiente sentencia SQL: [{sentencia_sql}]\nError: [{err.args[0]}]")
    
    return None



###############################################################################
# 2) VISTA
###############################################################################

def crear_marco_etiqueta(objeto_padre, texto_marco, posicion_x, posicion_y, ancho, alto):
    mi_recuadro = LabelFrame(objeto_padre, text=texto_marco)
    mi_recuadro.pack()
    mi_recuadro.place(x=posicion_x, y=posicion_y, width=ancho, height=alto)
    return mi_recuadro

def crear_etiqueta(objeto_padre, texto, posicion_x, posicion_y, fuente=fuente_normal):
    mi_etiqueta = Label(objeto_padre, text=texto, font=fuente)
    mi_etiqueta.pack()
    mi_etiqueta.place(x=posicion_x, y=posicion_y)
    return mi_etiqueta

def crear_campo_de_texto(objeto_padre, variable_relacionada, posicion_x, posicion_y, ancho, acepta_solo_numeros=False):
    campo_de_texto = Entry(objeto_padre)
    campo_de_texto.pack()
    campo_de_texto.config(textvariable=variable_relacionada, width=ancho, justify=CENTER)   # Por defecto el texto está centrado
    campo_de_texto.place(x=posicion_x, y=posicion_y)
    
    # Agregar validación de ingreso solo numérico de ser necesario
    if acepta_solo_numeros:
        campo_de_texto.configure(validate="key", validatecommand=(objeto_padre.register(es_numero_entero), "%S"))

    return campo_de_texto

def crear_boton(objeto_padre, texto_boton=None, imagen_boton=None, posicion_x=-1, posicion_y=-1, ancho=-1, alto=-1, nombre_funcion=None, argumentos=None):

    # Crea un botón con las dimensiones y posición especificados.
    # También asigna el nombre de función seleccionada para el evento click, y sus argumentos si los tiene (tupla o lista)
    # Si argumentos es None, entonces se asigna la función sin argumentos

    # Verificar argumentos
    if posicion_x == -1 or posicion_y == -1 or ancho == -1 or alto == -1 or nombre_funcion is None:
        return None
    
    if argumentos is not None and type(argumentos) != tuple:
        argumentos = tuple(argumentos)

    # Crear el botón y le asigna la función correspondiente
    if argumentos is None:
        nuevo_boton = Button(objeto_padre, command=nombre_funcion)
    else:
        nuevo_boton = Button(objeto_padre, command=lambda: nombre_funcion(argumentos))

    # Configurar los atributos del botón
    nuevo_boton.configure(width=ancho, height=alto, justify=CENTER) # Por defecto el texto estará centrado
    if texto_boton is not None:
        nuevo_boton.configure(text=texto_boton)    
    if imagen_boton is not None:
        nuevo_boton.configure(Image=imagen_boton)

    nuevo_boton.pack()
    nuevo_boton.place(x=posicion_x, y=posicion_y)

    return nuevo_boton

def mostrar_lista_de_materiales(registros_tabla_de_materiales):
    global treeview_materiales

    for fila in treeview_materiales.get_children():
        treeview_materiales.delete(fila)

    for registro in registros_tabla_de_materiales:
        treeview_materiales.insert("", "end", 
                                   text=str(registro[0]),
                                   values=(
                                   registro[1],
                                   str(registro[2]),
                                   str(registro[3]),
                                   str(registro[4]))
                                   )

    

def mostrar_lista_de_productos(registros_tabla_de_productos):
    global treeview_productos

    for fila in treeview_productos.get_children():
        treeview_productos.delete(fila)

    for registro in registros_tabla_de_productos:
        treeview_productos.insert("", "end", 
                                   text=str(registro[0]),
                                   values=(
                                   registro[1],)
                                   )
        
def crear_ventana_principal(ventana_principal):

    global treeview_materiales

    # Crear el contendor de tabs donde se desarrolla cada área de trabajo de la aplicación
    tabcontrol = ttk.Notebook(ventana_principal)
    tabcontrol.identify(x=140, y=10)
    tabcontrol.pack(expand=1, fill="both")

    fecha_actual = datetime.now()
    fecha_formateada = ("Operaciones del día {:02}/{:02}/{}".format(fecha_actual.day, fecha_actual.month, fecha_actual.year))

    # Mostrar la fecha actual en la parte inferior de la pantalla
    etiqueta_fecha = crear_etiqueta(ventana_principal, fecha_formateada, posicion_x=280, posicion_y=480, fuente=fuente_titulo_1)
    etiqueta_fecha.config(bg="purple")

    # Crear el menú principal
    menu_principal = Menu(ventana_principal)
    menu_archivo = Menu(menu_principal, tearoff=0)
    menu_archivo.add_command(label="Actualizar Stock", command=pedidos_actualizar_stock)
    menu_archivo.add_command(label="Acerca de", command=mostrar_version_aplicacion)
    menu_archivo.add_separator()
    menu_archivo.add_command(label="Salir", command=cerrar_aplicacion)
    menu_principal.add_cascade(label="Archivo", menu=menu_archivo)
    ventana_principal.config(menu=menu_principal)

    # Ubicar la imagen de la bandera Argentina en la esquina inferior-derecha de la pantalla
    ruta_imagen = os.path.join(DIRECTORIO_IMAGENES, "bandera.png")
    imagen = Image.open(ruta_imagen)
    contenedor_imagen = imagen.resize((80, 50))
    render = ImageTk.PhotoImage(contenedor_imagen)
    etiqueta = Label(ventana_principal, image=render)
    etiqueta.image = render
    etiqueta.place(x=805, y=470)


    return tabcontrol

def crear_ventana_materiales(tabcontrol):

    tab_materiales = ttk.Frame(tabcontrol, width=500, height=50)
    tabcontrol.add(tab_materiales, text='Materiales')

    # 2 - Sección Materiales
    marco_materiales = crear_marco_etiqueta(tab_materiales, "Gestión de Materiales", posicion_x=0, posicion_y=20, ancho=860, alto=400)
    
    # Etiquetas
    crear_etiqueta(marco_materiales, "Descripción", posicion_x=10, posicion_y=10)
    crear_etiqueta(marco_materiales, "Stock Actual", posicion_x=10, posicion_y=40)
    crear_etiqueta(marco_materiales, "Nivel Reposición", posicion_x= 10, posicion_y=70)
    crear_etiqueta(marco_materiales, "Demora Reposición", posicion_x=10, posicion_y=100)
    crear_etiqueta(marco_materiales, "* Doble click para seleccionar el material", posicion_x=10, posicion_y=360).configure(font=Font(size=10))

    # Campos de texto
    crear_campo_de_texto(marco_materiales, variable_relacionada=diccionario_materiales["descripcion"], posicion_x=150, posicion_y=10, ancho=35).configure(justify=LEFT, bg='blue')
    crear_campo_de_texto(marco_materiales, variable_relacionada=diccionario_materiales["stock_actual"], posicion_x=150, posicion_y=40, ancho=5, acepta_solo_numeros=True)
    crear_campo_de_texto(marco_materiales, variable_relacionada=diccionario_materiales["stock_reposicion"], posicion_x=150, posicion_y=70, ancho=5, acepta_solo_numeros=True)
    crear_campo_de_texto(marco_materiales, variable_relacionada=diccionario_materiales["demora_reposicion"], posicion_x=150, posicion_y=100, ancho=5, acepta_solo_numeros=True)

    # Botones para administrar los campos de un material seleccionado o que se está dando de alta
    crear_boton(objeto_padre=marco_materiales, texto_boton="Limpiar", imagen_boton=None, posicion_x=700, posicion_y=10, ancho=ancho_boton_normal, alto=1, nombre_funcion=materiales_limpiar_campos, argumentos=None)
    crear_boton(objeto_padre=marco_materiales, texto_boton="Agregar", imagen_boton=None, posicion_x=700, posicion_y=40, ancho=ancho_boton_normal, alto=1, nombre_funcion=materiales_agregar_material, argumentos=None)
    crear_boton(objeto_padre=marco_materiales, texto_boton="Actualizar", imagen_boton=None, posicion_x=700, posicion_y=70, ancho=ancho_boton_normal, alto=1, nombre_funcion=materiales_actualizar_material, argumentos=None)
    crear_boton(objeto_padre=marco_materiales, texto_boton="Eliminar", imagen_boton=None, posicion_x=700, posicion_y=100, ancho=ancho_boton_normal, alto=1, nombre_funcion=materiales_eliminar_material, argumentos=None)

    # Botones de ayuda
    crear_boton(objeto_padre=marco_materiales, texto_boton="?", imagen_boton=None, posicion_x=480, posicion_y=10, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Campo Descripción", "Información descriptiva sobre el material"])
    crear_boton(objeto_padre=marco_materiales, texto_boton="?", imagen_boton=None, posicion_x=210, posicion_y=40, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Campo Stock Actual", "Cantidad de unidades en stock del material"])
    crear_boton(objeto_padre=marco_materiales, texto_boton="?", imagen_boton=None, posicion_x=210, posicion_y=70, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Campo Nivel Reposición", "Cuando el stock es menor o igual a esta cantidad, se realiza el pedido de reposición del material"])
    crear_boton(objeto_padre=marco_materiales, texto_boton="?", imagen_boton=None, posicion_x=210, posicion_y=100, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Campo Demora Reposición", "Número de días que debe esperarse para recibir el material una vez que se haya hecho el pedido de reposición"])
    crear_boton(objeto_padre=marco_materiales, texto_boton="?", imagen_boton=None, posicion_x=780, posicion_y=10, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Limpiar Formulario", "Elimina todos los campos de alta / baja / modificación / consulta de materiales"])
    crear_boton(objeto_padre=marco_materiales, texto_boton="?", imagen_boton=None, posicion_x=780, posicion_y=40, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Agregar Material", "Crea un nuevo material en la base de datos. Todos los campos del formulario deben haberse completado para poder dar de alta un nuevo material"])
    crear_boton(objeto_padre=marco_materiales, texto_boton="?", imagen_boton=None, posicion_x=780, posicion_y=70, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Actualizar Material", "Actualiza en la base de datos la información del material mostrado en el formulario de materiales"])
    crear_boton(objeto_padre=marco_materiales, texto_boton="?", imagen_boton=None, posicion_x=780, posicion_y=100, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Eliminar Material", "Elimina de forma permanente el material en la base de datos.\nPara ello, el material no debe estar asociado a ningún producto de la sección Manufactura."])
  
    # TreeView de materiales
    treeview_materiales = ttk.Treeview(marco_materiales)
    treeview_materiales["columns"] = ("col1", "col2", "col3", "col4")
    treeview_materiales.heading("#0", text="ID")
    treeview_materiales.heading("col1", text="Descripción")
    treeview_materiales.heading("col2", text="Stock Actual")
    treeview_materiales.heading("col3", text="Nivel de Reposición")
    treeview_materiales.heading("col4", text="Demora Reposición (días)")
    treeview_materiales.column("#0", width=40, minwidth=40, anchor=N)
    treeview_materiales.column("col1", width=300, minwidth=300, anchor=W)
    treeview_materiales.column("col2", width=150, minwidth=150, anchor=N)
    treeview_materiales.column("col3", width=150, minwidth=150, anchor=N)
    treeview_materiales.column("col4", width=150, minwidth=150, anchor=N)
    treeview_materiales.pack()
    treeview_materiales.place(x=10, y=150, width=830)
    treeview_materiales.bind("<Double-1>", click_en_material)

    # Agregar scrollbar al treeview
    scrollbar_materiales = Scrollbar(marco_materiales)
    scrollbar_materiales.pack(side=RIGHT, fill=Y)
    scrollbar_materiales.place(x=840, y=150, height=210, width=10)
    scrollbar_materiales.config(command=treeview_materiales.yview)
    treeview_materiales.config(yscrollcommand=scrollbar_materiales.set)

    return treeview_materiales

def crear_ventana_productos(tabcontrol):

    tab_productos = ttk.Frame(tabcontrol, width=500)
    tabcontrol.add(tab_productos, text='Productos')

    # 3 - Sección Productos
    marco_productos = crear_marco_etiqueta(tab_productos, "Gestión de Productos", posicion_x=0, posicion_y=20, ancho=860, alto=400)
    
    # Etiquetas
    crear_etiqueta(marco_productos, "Descripción", posicion_x=10, posicion_y=10)
    crear_etiqueta(marco_productos, "Productos", posicion_x=10, posicion_y=60)
    crear_etiqueta(marco_productos, "Materiales usados por el producto", posicion_x=400, posicion_y=60)
    crear_etiqueta(marco_productos, "Material", posicion_x=10, posicion_y=300)
    crear_etiqueta(marco_productos, "Cantidad", posicion_x=10, posicion_y=330)
    crear_etiqueta(marco_productos, "* Doble click para seleccionar el producto", posicion_x=10, posicion_y=360).configure(font=Font(size=10))

    # Campos de texto
    crear_campo_de_texto(marco_productos, variable_relacionada=diccionario_productos["descripcion"], posicion_x=85, posicion_y=10, ancho=30).configure(justify=LEFT, bg='blue')
    crear_campo_de_texto(marco_productos, variable_relacionada=entry_cantidad_de_material, posicion_x=80, posicion_y=325, ancho=5, acepta_solo_numeros=True).configure(justify=CENTER)

    # Botones para administrar los campos de un producto seleccionado o que se está dando de alta
    crear_boton(objeto_padre=marco_productos, texto_boton="Limpiar", imagen_boton=None, posicion_x=440, posicion_y=10, ancho=ancho_boton_normal, alto=1, nombre_funcion=productos_limpiar_campos, argumentos=None)
    crear_boton(objeto_padre=marco_productos, texto_boton="Agregar", imagen_boton=None, posicion_x=590, posicion_y=10, ancho=ancho_boton_normal, alto=1, nombre_funcion=productos_agregar_producto, argumentos=None)
    crear_boton(objeto_padre=marco_productos, texto_boton="Eliminar", imagen_boton=None, posicion_x=730, posicion_y=10, ancho=ancho_boton_normal, alto=1, nombre_funcion=productos_eliminar_producto, argumentos=None)
    crear_boton(objeto_padre=marco_productos, texto_boton="Asociar >>", imagen_boton=None, posicion_x=180, posicion_y=325, ancho=ancho_boton_xl, alto=1, nombre_funcion=productos_asociar_material, argumentos=None)
    crear_boton(objeto_padre=marco_productos, texto_boton="Desasociar", imagen_boton=None, posicion_x=400, posicion_y=325, ancho=ancho_boton_xl, alto=1, nombre_funcion=productos_desasociar_material, argumentos=None)

    # Botones de ayuda
    crear_boton(objeto_padre=marco_productos, texto_boton="?", imagen_boton=None, posicion_x=370, posicion_y=10, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Campo Descripción", "Información descriptiva sobre el producto"])
    crear_boton(objeto_padre=marco_productos, texto_boton="?", imagen_boton=None, posicion_x=510, posicion_y=10, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Limpiar Descripción", "Elimina el texto Descripción del formulario (esto no elimina el producto de la base de datos)"])
    crear_boton(objeto_padre=marco_productos, texto_boton="?", imagen_boton=None, posicion_x=660, posicion_y=10, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Agregar Producto", "Crea un nuevo producto en la base de datos."])
    crear_boton(objeto_padre=marco_productos, texto_boton="?", imagen_boton=None, posicion_x=800, posicion_y=10, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Eliminar Producto", "Elimina un producto y sus relaciones a materiales usados."])
    crear_boton(objeto_padre=marco_productos, texto_boton="?", imagen_boton=None, posicion_x=270, posicion_y=325, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Asociar Material", "Asocia al producto el material y cantidad seleccionados."])
    crear_boton(objeto_padre=marco_productos, texto_boton="?", imagen_boton=None, posicion_x=490, posicion_y=325, ancho=ancho_boton_ayuda, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Desasociar Material", "Elimina la asociación entre el producto seleccionado y el material resaltado en la lista de materiales por producto."])

    # TreeView de productos
    treeview_productos = ttk.Treeview(marco_productos)
    treeview_productos["columns"] = ("col1")
    treeview_productos.heading("#0", text="ID")
    treeview_productos.heading("col1", text="Producto")
    treeview_productos.column("#0", width=30, minwidth=30, anchor=N)
    treeview_productos.column("col1", width=350, minwidth=250, anchor=W)
    treeview_productos.pack()
    treeview_productos.place(x=10, y=80, width=350, height=210)
    treeview_productos.bind("<Double-1>", click_en_producto)

    treeview_materiales_por_producto = ttk.Treeview(marco_productos)
    treeview_materiales_por_producto["columns"] = ("col1", "col2")
    treeview_materiales_por_producto.heading("#0", text="ID")
    treeview_materiales_por_producto.heading("col1", text="Material")
    treeview_materiales_por_producto.heading("col2", text="Cantidad")
    treeview_materiales_por_producto.column("#0", width=30, minwidth=30, anchor=N)
    treeview_materiales_por_producto.column("col1", width=300, minwidth=300, anchor=W)
    treeview_materiales_por_producto.column("col2", width=30, minwidth=30, anchor=N)
    treeview_materiales_por_producto.pack()
    treeview_materiales_por_producto.place(x=400, y=80, width=435, height=210)

    # Agregar scrollbar a ambos objetos treeview
    scrollbar_productos = Scrollbar(marco_productos)
    scrollbar_productos.pack(side=RIGHT, fill=Y)
    scrollbar_productos.place(x=360, y=80, width=10, height=210)
    scrollbar_productos.config(command=treeview_productos.yview)
    treeview_productos.config(yscrollcommand=scrollbar_productos.set)
    
    scrollbar_materiales_por_producto = Scrollbar(marco_productos)
    scrollbar_materiales_por_producto.pack(side=RIGHT, fill=Y)
    scrollbar_materiales_por_producto.place(x=835, y=80, width=10, height=210)
    scrollbar_materiales_por_producto.config(command=treeview_materiales_por_producto.yview)
    treeview_materiales_por_producto.config(yscrollcommand=scrollbar_materiales_por_producto.set)

    # Combobox de materiales
    combobox_materiales = ttk.Combobox(marco_productos, state='readonly', width=23)
    combobox_materiales.place(x=80, y=295)
  
    return treeview_productos, treeview_materiales_por_producto, combobox_materiales

def crear_ventana_pedidos(tabcontrol):

    tab_pedidos = ttk.Frame(tabcontrol, width=500)
    tabcontrol.add(tab_pedidos, text='Pedidos')

    # 3 - Sección Productos
    marco_pedidos = crear_marco_etiqueta(tab_pedidos, "Gestión de Pedidos", posicion_x=0, posicion_y=20, ancho=860, alto=400)

    # Combobox de productos en venta
    combobox_productos = ttk.Combobox(marco_pedidos, state='readonly', width=23)
    combobox_productos.place(x=80, y=20)

    # Etiquetas
    crear_etiqueta(marco_pedidos, "Productos", posicion_x=10, posicion_y=20)
    crear_etiqueta(marco_pedidos, "PROCESO DE REPOSICIÓN DE PEDIDOS", posicion_x=10, posicion_y=150, fuente=fuente_titulo_2)
    crear_etiqueta(marco_pedidos, """
    Al presionar el botón 'Actualizar Stock' se ejecuta el proceso de actualización de stock de materiales.
    La reposición se realiza sobre aquellos materiales cuyo stock actual sea inferior a su nivel de reposición.
    Cada vez que se presiona el botón, el stock de materiales que se encuentre por debajo de su nivel de reposición
    será incrementado en 10 unidades.
    """, posicion_x=10, posicion_y=170, fuente=fuente_titulo_2).configure(justify=LEFT)

    # Botones para administrar los campos de un producto seleccionado o que se está dando de alta
    crear_boton(objeto_padre=marco_pedidos, texto_boton="Calcular Pedido", imagen_boton=None, posicion_x=440, posicion_y=20, ancho=ancho_boton_xxl, alto=1, nombre_funcion=pedidos_procesar_pedido, argumentos=None)
    crear_boton(objeto_padre=marco_pedidos, texto_boton="Actualizar Stock", imagen_boton=None, posicion_x=440, posicion_y=280, ancho=ancho_boton_xxl, alto=1, nombre_funcion=pedidos_actualizar_stock, argumentos=None)

    # Botones de ayuda
    crear_boton(objeto_padre=marco_pedidos, texto_boton="?", imagen_boton=None, posicion_x=320, posicion_y=20, ancho=1, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Lista de Productos", "Permite seleccionar el producto sobre el cual se quiere planificar el tiempo en el cual el pedido estará listo"])
    crear_boton(objeto_padre=marco_pedidos, texto_boton="?", imagen_boton=None, posicion_x=570, posicion_y=20, ancho=1, alto=1, nombre_funcion=mostrar_mensaje, argumentos=["Calcular Pedido", "Verifica si existe demora para producir el pedido en función del stock de materiales disponibles"])
 
    return combobox_productos

def actualizar_combobox_de_materiales():
    global conexion_bd, combobox_materiales

    valores_combobox = []
    materiales = materiales_recuperar_materiales(conexion_bd)
    for id, material, stock, alerta, demora in materiales:
        valores_combobox.append(material)

    combobox_materiales['values'] = valores_combobox

def mostrar_version_aplicacion():
    mostrar_mensaje(["Acerca de", """
    GEMPROP v1.0
    Autor: Hernán Buzzi

    Desarrollado como Trabajo Práctico Final del módulo Python 3 - Nivel Inicial
    Diplomatura en Python - UTN

    Año 2023
    """])

def cerrar_aplicacion():
    global ventana_principal
    if askyesno("Salir", "Confirma que desea cerrar esta aplicación?"):
        ventana_principal.quit()

###############################################################################
# 3) CONTROLADOR
###############################################################################

def es_numero_entero(texto):
    # Devuelve True si el valor recibido solo contiene dígitos numéricos,
    # caso contrario devuelve False
    if type(texto) == int:  # El tipo de datos ya es entero
        return True
    if texto is None:       # El campo está vacío (el usuario borró el valor)
        return False
    patron_numerico = re.compile("^[0-9]+$")    # Aceptar solo dígitos numéricos
    resultado = patron_numerico.match(texto)
    if resultado is None:
        return False   
    return True

def materiales_limpiar_campos():
    global diccionario_materiales

    # Limpia los campos de texto de la sección Materiales
    diccionario_materiales["id"].set(0)
    diccionario_materiales["descripcion"].set("")
    diccionario_materiales["stock_actual"].set(0)
    diccionario_materiales["stock_reposicion"].set(0)
    diccionario_materiales["demora_reposicion"].set(0)

def formulario_de_materiales_correcto():
    global diccionario_materiales
    # Verifica si los campos del formulario de materiales son válidos, es decir que haya una descripción
    # que los campos numéricos tengan un valor decimal mayor a cero.

    # Validar si se completaron todos los campos del material, solo en ese caso se inserta el registro
    for clave in diccionario_materiales:
        try:
            valor_actual = diccionario_materiales[clave].get()  # Se intenta obtener el valor del campo
        except:
            mostrar_mensaje(["Error de datos", "Todos los campos del formulario de materiales son requeridos"])
            return False

    if len(diccionario_materiales["descripcion"].get()) == 0:   # Verificar que se ingresó la descripción
        mostrar_mensaje(["Error de datos", "La descripción del material es requerida!"])
        return False

    # Verificar que ningún número sea cero
    if diccionario_materiales["stock_actual"].get() == 0 or\
        diccionario_materiales["stock_reposicion"].get() == 0 or\
        diccionario_materiales["demora_reposicion"].get() == 0:
        mostrar_mensaje(["Error de datos", "Los valores de stock actual, nivel de reposición y unidades de reposición deben ser mayor a cero!"])
        return False

    return True

def materiales_agregar_material():
    global conexion_bd, diccionario_materiales

    # Verificar que no haya errores en el formulario de materiales antes de insertar el registro
    if not formulario_de_materiales_correcto():
        return False

    # Verificar que no exista un material con la misma descripción (case sensitive)
    sql = "SELECT COUNT(id) FROM materiales WHERE descripcion = ?"
    datos = (diccionario_materiales["descripcion"].get(),)
    registros_leidos = ejecutar_consulta_sql(conexion_bd, sql, datos)
    if registros_leidos is not None:
        if registros_leidos[0][0] > 0:
            mostrar_mensaje(["Error", "El material ya existe en la base de datos"])
            return False

    # Cumplidas todas las validaciones, se procede a agregar el registro del nuevo material
    if materiales_insertar_registro_material(conexion_bd):
        registros = materiales_recuperar_materiales(conexion_bd)
        mostrar_lista_de_materiales(registros)  # Actualizar el TreeView de materiales
        materiales_limpiar_campos()             # Limpiar el formulario de materiales
        actualizar_combobox_de_materiales()     # Rehacer la lista de materiales mostrada en el combobox de productos
        registrar_evento(f"Se agregó el material [{diccionario_materiales['descripcion'].get()}] a la base de datos")
        mostrar_mensaje(["El material fue agregado exitosamente a la base de datos!"])
    else:
        registrar_evento(f"Error agregando el material [{diccionario_materiales['descripcion'].get()}] a la base de datos")
        mostrar_mensaje(["Error", "No se pudo agregar el material a la base de datos"])
        return False

    return True

def materiales_actualizar_material():

    global conexion_bd, diccionario_materiales

    # Verificar que no haya errores en el formulario de materiales antes de insertar el registro
    if not formulario_de_materiales_correcto():
        return False

    id_material = 0
    try:
        id_material = diccionario_materiales["id"].get()
    except:
        return False    # Esta excepción se da si nunca se leyó un registro antes de querer actualizarlo

    # Verificar si el usuario modificó algo, de otra manera no tiene sentido actualizar el registro sin cambios
    registro = materiales_buscar_material(conexion_bd, id_material)
    if registro is None:
        return False    # Registro a actualizar no encontrado

    # Actualizar el material
    if not materiales_actualizar_registro_material(conexion_bd, id_material):
        return False    # No se pudo actualizar el material
    
    # Refrescar la lista de materiales para que se refleje el cambio
    mostrar_lista_de_materiales(materiales_recuperar_materiales(conexion_bd))

    # Refrescar la lista de materiales asociados a productos
    productos_mostrar_materiales_asociados(conexion_bd)
    actualizar_combobox_de_materiales()
    
    mostrar_mensaje(["Materiales", "El material fue actualizado correctamente!"])
    return True

def materiales_eliminar_material():
    global conexion_bd

    descripcion_material = diccionario_materiales["descripcion"].get()
    id_material = diccionario_materiales["id"].get()

    # Verificar que se haya seleccionado un material
    if descripcion_material == "":   # No hay ningún material seleccionado
        mostrar_mensaje(["Error", "Debe seleccionar un material para poder borrarlo"])
        return False
    
    # Verificar que el material no esté siendo usado por algún producto (de otra forma, este no puede eliminarse)
    resultado = ejecutar_consulta_sql(conexion_bd, "SELECT COUNT(id_material) FROM materiales_por_producto WHERE id_material = ?", (id_material,))
    if int(resultado[0][0]) > 0:
        mostrar_mensaje(["Error", "El material seleccionado está asociado a uno o mas productos y no puede eliminarse.\nElimine la relación del material con los productos e intente nuevamente."])
        return False
    
    # Confirmar que se va a eliminar el material
    if not askyesno("Eliminar material", f"Confirma que desea eliminar el siguiente material?\n[{descripcion_material}]"):
        return False
    
    # Eliminar el material
    sql = "DELETE FROM materiales WHERE id = ?"
    datos = (id_material,)
    if ejecutar_sentencia_sql(conexion_bd, sql, datos) is not None:
        mostrar_mensaje(["Material Eliminado", "El material seleccionado ha sido eliminado de la base de datos del sistema"])

    # Actualizar el treeview de materiales y limpiar el formulario de material seleccionado
    mostrar_lista_de_materiales(materiales_recuperar_materiales(conexion_bd))
    materiales_limpiar_campos()

    actualizar_combobox_de_materiales()

    return True

def productos_limpiar_campos():
    global diccionario_productos
    
    # Limpia el campo descripción y el id asociado de la sección Productos
    diccionario_productos["id"].set(0)
    diccionario_productos["descripcion"].set("")

def productos_agregar_producto():
    global conexion_bd, diccionario_productos

    # Verificar que se haya ingresado una descripción para el nuevo producto
    try:
        valor_actual = diccionario_productos["descripcion"].get()
    except:
        mostrar_mensaje(["Error de datos", "La descripción es requerida para crear un nuevo producto"])
        return False
    if len(diccionario_productos["descripcion"].get()) == 0:   # Verificar que se ingresó la descripción
        mostrar_mensaje(["Error de datos", "La descripción es requerida para crear un nuevo producto"])
        return False

    # Verificar que no exista un producto con la misma descripción (case sensitive)
    sql = "SELECT COUNT(id) FROM productos WHERE descripcion = ?"
    datos = (diccionario_productos["descripcion"].get(),)
    resultado_consulta = ejecutar_consulta_sql(conexion_bd, sql, datos)
    if resultado_consulta is not None and int(resultado_consulta[0][0]) > 0:
        mostrar_mensaje(["Error", "El producto ya existe en la base de datos"])
        return False

    # Cumplidas todas las validaciones, se procede a agregar el registro del nuevo producto
    if productos_insertar_registro_producto(conexion_bd) is not None:
        registros = productos_recuperar_productos(conexion_bd)
        mostrar_lista_de_productos(registros)  # Actualizar el TreeView de productos
        productos_limpiar_campos()             # Limpiar el formulario de productos
        registrar_evento(f"Se agregó el producto [{diccionario_productos['descripcion'].get()}] a la base de datos")
        mostrar_mensaje(["El producto fue agregado exitosamente a la base de datos!"])
    else:
        registrar_evento(f"Error agregando el producto [{diccionario_productos['descripcion'].get()}] a la base de datos")
        mostrar_mensaje(["Error", "No se pudo agregar el producto a la base de datos"])
        return False

    # Actualizar la lista de productos en el combobox del tab de pedidos
    pedidos_recuperar_productos(conexion_bd)

    return True

def productos_asociar_material():
    global conexion_bd, combobox_materiales, entry_cantidad_de_material, treeview_materiales_por_producto, diccionario_productos

    # Primero se verifica que se haya seleccionado un producto y un material, y que se haya ingresado una cantidad de material
    if diccionario_productos["descripcion"].get() == "":
        mostrar_mensaje(['Atención', 'Debe seleccionar un producto antes de poder asociarle materiales'])
        return False

    if combobox_materiales.current() == -1: # -1 significa que no hay nada seleccionado en el combo box
        mostrar_mensaje(['Atención', 'Debe seleccionar un material de la lista desplegable de materiales'])
        return False
    if entry_cantidad_de_material.get() == 0:     # Se seleccionó un material pero no se indicó la cantidad a usar en el producto
        mostrar_mensaje(['Atención', 'Debe indicar la cantidad de unidades del material seleccionadoseleccionar un material de la lista desplegable de materiales'])
        return False

    # Luego verificamos que el material (por su descripción) no se encuentre previamente agregado a la lista de materiales asociados
    material_seleccionado = combobox_materiales.get()
    if len(treeview_materiales_por_producto.get_children()) > 0:   # Si hay materiales en el treeview
        id_materiales_ya_asociados = treeview_materiales_por_producto.get_children()    # Se obtienen los id's de cada material previamente asociado al producto
        for id_material in id_materiales_ya_asociados:
            if treeview_materiales_por_producto.item(id_material)['values'][0] == material_seleccionado:          # Si devuelve True, se está intentando agregar un material previamente asociado al producto
                mostrar_mensaje(['Atención', 'Este material ya se encuentra asociado al producto seleccionado'])
                return False

    # Confirmar que se quiere agregar el material
    if not askyesno("Asociar material", f"Confirma que desea asociar el siguiente material al producto seleccionado?\n\nProducto: [{diccionario_productos['descripcion'].get()}]\nMaterial: [{material_seleccionado}]"):
        return False

    # Agregar el material y su cantidad al treeview de materiales asociados al producto
    productos_asociar_material_a_producto(conexion_bd, material_seleccionado, entry_cantidad_de_material.get())
    
    return True

def productos_desasociar_material():
    global treeview_materiales_por_producto, diccionario_productos

    # Verificar si se seleccionó un material de la lista de materials por producto
    if treeview_materiales_por_producto.item(treeview_materiales_por_producto.focus())['values'] == "":
        mostrar_mensaje(["Material no seleccionado", "Primero debe seleccionar un material de la listas de materiales asociados al producto"])
        return False
    material_seleccionado = treeview_materiales_por_producto.item(treeview_materiales_por_producto.focus())['values'][0]
    # Confirmar la desasociación del material

    if not askyesno("Desasociar material", f"Confirma que desea desasociar el siguiente material del producto seleccionado?\n\nProducto: [{diccionario_productos['descripcion'].get()}]\nMaterial: [{material_seleccionado}]"):
        return False
    
    # Eliminar la relación entre el material y el producto
    productos_desasociar_material_del_producto(conexion_bd, material_seleccionado)
    
    return True

def productos_eliminar_producto():
    global conexion_bd

    descripcion_producto = diccionario_productos["descripcion"].get()
    id_producto = diccionario_productos["id"].get()

    # Verificar que se haya seleccionado un producto
    if descripcion_producto == "":   # No hay ningún producto seleccionado
        mostrar_mensaje(["Error", "Debe seleccionar un producto para poder borrarlo"])
        return False
    
    # Confirmar que se va a eliminar el producto y la relación a los materiales que utiliza
    if not askyesno("Eliminar producto", f"Confirma que desea eliminar el siguiente producto y sus relaciones con los materiales usados?\n[{descripcion_producto}]"):
        return False
    
    # Eliminar la relación entre el producto y los materiales (si las hay)
    sql = "DELETE FROM materiales_por_producto WHERE id_producto = ?"
    datos = (id_producto,)
    if ejecutar_sentencia_sql(conexion_bd, sql, datos) is None:
        mostrar_mensaje(["Error", "Error eliminando materiales asociados al producto. Verifique que no haya un bloqueo de registros en la base de datos."])
        return False

    # Eliminar el producto
    sql = "DELETE FROM productos WHERE id = ?"
    datos = (id_producto,)
    if ejecutar_sentencia_sql(conexion_bd, sql, datos) is None:
        mostrar_mensaje(["Error", "Error eliminando el producto. Verifique que no haya un bloqueo de registros en la base de datos."])
        return False

    # Refrescar el treeview de productos y el de materiales usados por producto
    diccionario_productos["id"].set(0)
    diccionario_productos["descripcion"].set("")
    mostrar_lista_de_productos(productos_recuperar_productos(conexion_bd))      # Treeview de productos
    productos_mostrar_materiales_asociados(conexion_bd)                         # Treeview de materiales asociados

    # Refrescar el combobox de productos en el tab de pedidos
    pedidos_recuperar_productos(conexion_bd)

    mostrar_mensaje(["Producto Eliminado", "El producto seleccionado ha sido eliminado de la base de datos del sistema"])
    return True

def pedidos_procesar_pedido():
    global combobox_productos, conexion_bd
    # Verificar que se seleccionó un producto en el combobox de productos
    if combobox_productos.current() == -1:
        mostrar_mensaje(["Material no seleccionado", "Debe seleccionar un producto para calcular si existe demora en la entrega"])
        return False
    producto_seleccionado = combobox_productos.get()

    # El primer paso es obtener el id de producto en base a su descripción
    sql = "SELECT id FROM productos WHERE descripcion = ?"
    id_producto = int(ejecutar_consulta_sql(conexion_bd, sql, (producto_seleccionado,))[0][0])
    
    # El segundo paso requiere recuperar la información de los materiales utilizados para fabricar el producto, a fin de saber si hay stock suficiente de todos ellos.
    # Se utiliza un JOIN entre 'materiales' y 'materiales_por_producto' para saber además cuántas unidades de cada material se requieren.
    sql = """
        SELECT m.id AS 'id_material', m.descripcion AS 'descripcion_material', m.stock_actual, r.cantidad_de_unidades AS 'unidades_necesarias', m.demora_reposicion, p.descripcion AS 'descripcion_producto'
        FROM materiales m
        INNER JOIN materiales_por_producto r
        ON m.id = r.id_material
        INNER JOIN productos p
        ON r.id_producto = p.id
        WHERE p.id = ?
        """
    datos = (id_producto,)
    registros = ejecutar_consulta_sql(conexion_bd, sql, datos)

    # Se analiza e informa si hay stock suficiente de todos los productos, o si se espera una demora para producir el producto solicitado
    demora_planificada = False
    demora_maxima = 0
    for material in registros:
        stock_actual = material[2]
        stock_necesario = material[3]
        if stock_actual < stock_necesario:   # Habrá una demora por al menos un material para el cual no hay stock suficiente
            demora_planificada = True
            demora_material_actual = material[4]
            if demora_maxima < demora_material_actual:
                demora_maxima = demora_material_actual
    
    # Se evalúa si puede producirse en tiempo el producto, de otra forma se informa cuál será la espera total por el mismo
    if demora_planificada and \
        not askyesno("No hay stock suficiente", f"Hay una demora de {demora_maxima} día(s) para producir este producto. Continuar con el pedido?"):
        return False
    
    for material in registros:
        id_material = material[0]
        stock_actual = material[2]
        stock_necesario = material[3]
        nuevo_stock_actual = stock_actual - stock_necesario
        sql = "UPDATE materiales SET stock_actual = ? WHERE id = ?"
        datos = (nuevo_stock_actual, id_material)
        if ejecutar_sentencia_sql(conexion_bd, sql, datos) is None:
            registrar_evento(f"Error actualizando el material con id=[{id_material}]")
        else:
            registrar_evento(f"Stock de material actualizado - id=[{id_material}] - stock anterior=[{stock_actual}] - nuevo nivel de stock=[{nuevo_stock_actual}]")

    # Actualizar el treeview de materiales del tab de materiales
    mostrar_lista_de_materiales(materiales_recuperar_materiales(conexion_bd))

    # Informar sobre el procedimiento de pedido completado
    mostrar_mensaje(["Pedido generado", "El pedido ha sido generado, y el stock de materiales usados por el producto fue actualizado"])

    return True

###############################################################################

nombre_sistema_operativo = platform.system()
if nombre_sistema_operativo == 'Darwin':
    nombre_sistema_operativo = 'MacOS'
aplicar_ajustas_por_sistema_operativo(nombre_sistema_operativo)
registrar_evento("Aplicación iniciada - Sistema operativo: " + nombre_sistema_operativo)

# Conectarse a la base de datos y asegurar que existan las tablas necesarias
# Por defecto, el nombre de la base de datos es gemprop.db, pero si se pasa un argumento por
# línea de comandos entonces se utiliza ese argumento como nombre de base de datos.
if len(sys.argv) > 1:
    nombre_base_de_datos = sys.argv[1]
conexion_bd = abrir_base_de_datos(nombre_base_de_datos)
crear_tabla_de_materiales(conexion_bd)
crear_tabla_de_productos(conexion_bd)
crear_tabla_de_materiales_por_producto(conexion_bd)

# Crear las ventanas en de gestión
tabcontrol = crear_ventana_principal(ventana_principal)
treeview_materiales = crear_ventana_materiales(tabcontrol)
treeview_productos, treeview_materiales_por_producto, combobox_materiales = crear_ventana_productos(tabcontrol)
combobox_productos = crear_ventana_pedidos(tabcontrol)
actualizar_combobox_de_materiales()

mostrar_lista_de_materiales(materiales_recuperar_materiales(conexion_bd))
mostrar_lista_de_productos(productos_recuperar_productos(conexion_bd))

pedidos_recuperar_productos(conexion_bd)

ventana_principal.mainloop()