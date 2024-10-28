import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import time

# ------------------------------------------------------
# Configuración de estilo
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Cargar el CSS con los estilos básicos
load_css('static/styles.css')

# Conectando a la base de datos
conn = sqlite3.connect('base_datos.db')
cursor = conn.cursor()

# Función para mostrar logotipo pequeño en la esquina superior izquierda
def mostrar_logotipo_pequeno():
    st.markdown("""
    <div style="display: flex; align-items: center; position: fixed; top: 10px; left: 10px;">
        <img src="Icono_030_PNG_BP.png" width="50">
    </div>
    """, unsafe_allow_html=True)

# Función para el pie de página
def footer():
    st.markdown("""
    <footer style="background-color: #f2f2f2; color: #333; padding: 10px; text-align: center;">
        <p>Mapa del sitio | Políticas de uso | Sobre nosotros | Contacto</p>
        <p>Instagram: 'www.instalink.com' | Facebook: 'www.facebooklink.com' | Teléfono: '+506 12345678'</p>
        <p>Correo: 'correo@correo.com'</p>
    </footer>
    """, unsafe_allow_html=True)

# Función para la página de inicio
def home():
    st.markdown("""
    <div style="text-align: center;">
        <img src="red_velvet_cake_mainwallpaper_001_BP.jpg" style="width: 100%; height: 200px; object-fit: cover;">
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center; font-family: Libre Baskerville;'>Arte dulce para saborear y admirar.</h1>", unsafe_allow_html=True)
    st.title("Bienvenido a Chou")
    st.markdown("""
        <p style="text-align: center;">
            En Chou, creamos repostería francesa artesanal, combinando técnica y creatividad. Ofrecemos tanto dulces como salados, todos con un toque artístico que convierte cada pieza en una pequeña obra maestra.
        </p>
    """, unsafe_allow_html=True)

    # Mostrar imágenes de Macaron y Baguette con sus nombres y precios
    col1, col2 = st.columns(2)
    with col1:
        st.image('Macaron_pin.jpg', use_column_width=True, caption="Macaron - $4")
    with col2:
        st.image('Baguette_pin.jpg', use_column_width=True, caption="Baguette - $2")

# Función para la sección de Consultar Recetas
def consultar_recetas(conn):
    st.title("Consultar Recetas")
    receta_nombre = st.text_input("Buscar receta por nombre")

    query = "SELECT id_receta, nombre_receta, instrucciones FROM recetas_BP WHERE nombre_receta LIKE ?"
    df_recetas = pd.read_sql_query(query, conn, params=(f"%{receta_nombre}%",))
    df_recetas["instrucciones"] = df_recetas["instrucciones"].apply(lambda x: x.encode('utf-8').decode('utf-8', 'ignore') if isinstance(x, str) else x)

    if df_recetas.empty:
        st.warning("No se encontraron recetas que coincidan con tu búsqueda.")
        return

    st.table(df_recetas[["nombre_receta", "instrucciones"]])  # Mostrar sin columna de índice

    receta_seleccionada = st.selectbox("Selecciona una receta", df_recetas["nombre_receta"].tolist())
    if receta_seleccionada:
        df_ingredientes = obtener_ingredientes_por_receta(conn, receta_seleccionada)
        cantidad_base = st.select_slider("Ajusta la cantidad base", options=[0.5, 1, 1.5, 2])
        df_ingredientes["Cantidad Ajustada"] = df_ingredientes["cantidad"] * cantidad_base
        df_ingredientes["Cantidad Ajustada"] = df_ingredientes["Cantidad Ajustada"].round(1)
        st.table(df_ingredientes[["nombre_ingrediente", "Cantidad Ajustada", "unidad_medida"]])

        instrucciones = obtener_instrucciones(conn, receta_seleccionada)
        st.text_area("Instrucciones:", instrucciones, height=150)

# Función para la sección Agregar Receta
def agregar_receta():
    st.title("Agregar Receta")
    nombre = st.text_input("Nombre de la receta")
    ingredientes_disponibles = obtener_ingredientes_disponibles(conn)
    ingredientes_seleccionados = st.multiselect("Selecciona los ingredientes", ingredientes_disponibles)
    cantidades = [st.number_input(f"Cantidad de {ingrediente}", min_value=0.1) for ingrediente in ingredientes_seleccionados]
    unidades = [st.selectbox(f"Unidad para {ingrediente}", ["gr", "ml", "unidades"]) for ingrediente in ingredientes_seleccionados]
    instrucciones = st.text_area("Instrucciones")
    
    if st.button("Agregar Receta"):
        agregar_receta_db(nombre, ingredientes_seleccionados, cantidades, unidades, instrucciones)
        st.success("Receta agregada exitosamente!")
    
    st.write("Resumen de la receta:")
    for ingrediente, cantidad, unidad in zip(ingredientes_seleccionados, cantidades, unidades):
        st.write(f"- {ingrediente}: {cantidad} {unidad}")

# Función para la sección Inventario
def inventario():
    st.title("Inventario")
    cursor.execute("SELECT * FROM inventario_BP")
    inventario_data = cursor.fetchall()
    df_inventario = pd.DataFrame(inventario_data, columns=["ID Ingrediente", "Ingrediente", "Cantidad", "Unidad"])
    st.table(df_inventario[["Ingrediente", "Cantidad", "Unidad"]])

    ingrediente = st.selectbox("Seleccionar ingrediente a modificar", df_inventario["Ingrediente"])
    nueva_cantidad = st.number_input("Nueva cantidad")
    nueva_unidad = st.selectbox("Nueva unidad", ["gr", "ml", "unidades"])

    if st.button("Modificar Ingrediente"):
        modificar_ingrediente(conn, ingrediente, nueva_cantidad, nueva_unidad)
        st.success("Ingrediente modificado exitosamente.")

# Función para la sección Registro de Datos
def registro_datos():
    st.title("Registro de datos")
    recetas = obtener_recetas()
    nombres = [receta[1] for receta in recetas]
    fig1 = plt.figure()
    plt.barh(nombres, [1] * len(nombres))
    plt.xlabel('Cantidad de recetas')
    plt.title('Visualización de Recetas')
    st.pyplot(fig1)

    cursor.execute("SELECT nombre_ingrediente, precio FROM ingredientes_BP")
    ingredientes_data = cursor.fetchall()
    df_ingredientes = pd.DataFrame(ingredientes_data, columns=["Ingrediente", "Precio"])
    fig2 = px.bar(df_ingredientes, x="Ingrediente", y="Precio", title="Costo de Ingredientes")
    st.plotly_chart(fig2)

# Función para agregar recetas a la base de datos
def agregar_receta_db(nombre, ingredientes, cantidades, unidades, instrucciones):
    cursor.execute('''INSERT INTO recetas_BP (nombre_receta, instrucciones) VALUES (?, ?)''', (nombre, instrucciones))
    conn.commit()
    for ingrediente, cantidad, unidad in zip(ingredientes, cantidades, unidades):
        cursor.execute('''INSERT INTO ingre_recetas_BP (id_receta, id_ingrediente, cantidad, unidad_medida) VALUES ((SELECT id_receta FROM recetas_BP WHERE nombre_receta = ?), (SELECT id_ingredientes FROM ingredientes_BP WHERE nombre_ingrediente = ?), ?, ?)''', (nombre, ingrediente, cantidad, unidad))
    conn.commit()
# Funcion para obtener ingredientes disponibles
def obtener_ingredientes_disponibles(conn):
    try:
        with conn.cursor() as cursor:  # Usar un contexto para el cursor
            cursor.execute("SELECT nombre_ingrediente FROM ingredientes_BP")
            ingredientes = [row[0] for row in cursor.fetchall()]
        return ingredientes
    except Exception as e:
        st.error(f"Error al obtener ingredientes: {e}")
        return []  # Retornar una lista vacía en caso de error

# Función para obtener todos las recetas
def obtener_recetas():
    cursor.execute("SELECT * FROM recetas_BP")
    return cursor.fetchall()

# Función para obtener los ingredientes por receta
def obtener_ingredientes_por_receta(conn, id_receta):
    query = '''
    SELECT i.nombre_ingrediente, ir.cantidad, ir.unidad_medida
    FROM ingre_recetas_BP AS ir
    JOIN ingredientes_BP AS i ON ir.id_ingrediente = i.id_ingredientes
    WHERE ir.id_receta = ?
    '''
    return pd.read_sql_query(query, conn, params=(id_receta,))

# Función para obtener instrucciones de una receta
def obtener_instrucciones(conn, id_receta):
    query = '''SELECT instrucciones FROM recetas_BP WHERE id_receta = ?'''
    pasos = pd.read_sql_query(query, conn, params=(id_receta,))
    return "\n".join(pasos["instrucciones"]

# Función para modificar los ingredientes de una receta existente en la base de datos
def modificar_ingrediente(conn, id_receta, nuevos_ingredientes, nuevas_cantidades, nuevas_unidades):
    # Primero, eliminamos los ingredientes actuales de la receta en la tabla ingre_recetas_BP
    cursor.execute("DELETE FROM ingre_recetas_BP WHERE id_receta = ?", (id_receta,))

    # Luego, insertamos los nuevos ingredientes con sus cantidades y unidades de medida
    for ingrediente, cantidad, unidad in zip(nuevos_ingredientes, nuevas_cantidades, nuevas_unidades):
        cursor.execute('''
            INSERT INTO ingre_recetas_BP (id_receta, id_ingrediente, cantidad, unidad_medida)
            VALUES (
                ?, 
                (SELECT id_ingredientes FROM ingredientes_BP WHERE nombre_ingrediente = ?), 
                ?, ?
            )
        ''', (id_receta, ingrediente, cantidad, unidad))
    conn.commit()

    print(f"Ingredientes para la receta con id {id_receta} han sido actualizados exitosamente.")

# Lógica de navegación
mostrar_logotipo_pequeno()
menu = ["Inicio", "Consultar recetas", "Agregar receta", "Inventario", "Registro de datos"]
selection = st.sidebar.selectbox("Bienvenido Chou. Usa el menú para navegar.", menu)

if selection == "Inicio":
    home()
elif selection == "Consultar recetas":
    consultar_recetas(conn)
elif selection == "Agregar receta":
    agregar_receta()
elif selection == "Inventario":
    inventario()
elif selection == "Registro de datos":
    registro_datos()

footer()  # Agregar pie de página
conn.close()  # Cerrar la conexión a la base de datos
