import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import time

# ------------------------------------------------------
# Función para cargar el archivo JavaScript
def load_js(file_name):
    with open(file_name) as f:
        st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)

# Llamando la función para cargar el JS
load_js('static/script.js')

# Función para cargar el archivo CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Llamando la función para cargar el CSS
load_css('static/styles.css')

# Conectando a la base de datos
conn = sqlite3.connect('base_datos.db')
cursor = conn.cursor()

# Función para mostrar logotipo con animación de letras colapsadas
def mostrar_logotipos():
    logotipo1 = st.empty()
    logotipo1.image("Icono_020_PNG_BP.png", use_column_width=True)
    time.sleep(1)
    for _ in range(6):  # Simulación de "colapso"
        logotipo1.image("Icono_020_PNG_BP.png", use_column_width=True)
        time.sleep(0.1)
    logotipo1.empty()
    logotipo2 = st.empty()
    logotipo2.image("Icono_030_PNG_BP.png", use_column_width=True)
    st.markdown("<h2 style='text-align: center;'>Arte dulce, para saborear y admirar.</h2>", unsafe_allow_html=True)

# Llamar a la función para mostrar los logotipos
mostrar_logotipos()

# Sistema de navegación
menu = ["Inicio", "Consultar recetas", "Agregar receta", "Inventario", "Registro de datos"]
selection = st.sidebar.selectbox("Bienvenido Chou. Usa el menú para navegar.", menu)

# Funciónes para cada página
def home():
    st.title("Bienvenido a Chou")
    st.markdown("<p style='text-align: center;'>En Chou, creamos repostería francesa artesanal, combinando técnica y creatividad. Ofrecemos tanto dulces como salados, todos con un toque artístico que convierte cada pieza en una pequeña obra maestra.</p>", unsafe_allow_html=True)

def consultar_recetas(conn):
    st.title("Consultar Recetas")
    receta_nombre = st.text_input("Buscar receta por nombre")

    query = "SELECT id_receta, nombre_receta, instrucciones FROM recetas_BP WHERE nombre_receta LIKE ?"
    df_recetas = pd.read_sql_query(query, conn, params=(f"%{receta_nombre}%",))
    if df_recetas.empty:
        st.warning("No se encontraron recetas que coincidan con tu búsqueda.")
        return
    st.table(df_recetas[["nombre_receta", "instrucciones"]])  # Tabla sin columna de índice

    receta_seleccionada = st.selectbox("Selecciona una receta", df_recetas["id_receta"].tolist())
    if receta_seleccionada:
        df_ingredientes = obtener_ingredientes_por_receta(conn, receta_seleccionada)
        cantidad_base = st.number_input("Ajusta la cantidad base", min_value=1, value=1)
        df_ingredientes["Cantidad Ajustada"] = df_ingredientes["cantidad"] * cantidad_base
        st.table(df_ingredientes[["nombre_ingrediente", "Cantidad Ajustada", "unidad_medida"]])

        instrucciones = obtener_instrucciones(conn, receta_seleccionada)
        st.text_area("Instrucciones:", instrucciones, height=150)

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
    st.write("Nombre:", nombre)
    st.write("Ingredientes:", ingredientes_seleccionados)
    st.write("Instrucciones:", instrucciones)

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

# Función para obtener ingredientes disponibles
def obtener_ingredientes_disponibles(conn):
    cursor.execute("SELECT nombre_ingrediente FROM ingredientes_BP")
    return [row[0] for row in cursor.fetchall()]

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
    return "\n".join(pasos["instrucciones"])

# Lógica de navegación entre páginas
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

# Cerrando la conexión a la base de datos
conn.close()
