import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import time

#------------------------------------------------------
# Funciones para cargar archivos JavaScript y CSS
def load_js(file_name):
    with open(file_name) as f:
        st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Llamar funciones para cargar archivos JS y CSS
load_js('static/script.js')
load_css('static/styles.css')

# Conectando a la base de datos
conn = sqlite3.connect('base_datos.db')
cursor = conn.cursor()

# Mostrar logotipos con animación
def mostrar_logotipos():
    logotipo1 = st.empty()
    logotipo1.image("Icono_020_PNG_BP.png", use_column_width=True)
    time.sleep(2)
    logotipo1.empty()
    logotipo2 = st.empty()
    logotipo2.image("Icono_030_PNG_BP.png", use_column_width=True)

mostrar_logotipos()

# Sistema de navegación
menu = ["Inicio", "Consultar recetas", "Agregar receta", "Inventario", "Registro de datos"]
selection = st.sidebar.selectbox("Bienvenido Chou. Usa el menú para navegar.", menu)

# Función principal de la página de inicio
def home():
    st.markdown("<h2 style='text-align: center;'>Arte dulce, para saborear y admirar.</h2>", unsafe_allow_html=True)
    st.title("Bienvenido a Chou")
    st.markdown("<p style='text-align: center;'>En Chou, creamos repostería francesa artesanal...</p>", unsafe_allow_html=True)

# Función para consultar recetas
def consultar_recetas(conn):
    st.title("Consultar Recetas")
    receta_nombre = st.text_input("Buscar receta por nombre")
    
    query = "SELECT id_receta, nombre_receta, instrucciones FROM recetas_BP WHERE nombre_receta LIKE ?"
    df_recetas = pd.read_sql_query(query, conn, params=(f"%{receta_nombre}%",))

    if df_recetas.empty:
        st.warning("No se encontraron recetas que coincidan con tu búsqueda.")
    else:
        st.table(df_recetas[["nombre_receta", "instrucciones"]])
        
        receta_seleccionada = st.selectbox("Selecciona una receta", df_recetas["id_receta"].tolist())
        
        if receta_seleccionada:
            df_ingredientes = obtener_ingredientes_por_receta(conn, receta_seleccionada)
            cantidad_base = st.number_input("Ajusta la cantidad base", min_value=1, value=1)
            df_ingredientes["Cantidad Ajustada"] = df_ingredientes["cantidad"] * cantidad_base
            st.table(df_ingredientes[["id_ingrediente", "Cantidad Ajustada", "unidad_medida"]])
            
            instrucciones = obtener_instrucciones(conn, receta_seleccionada)
            st.text_area("Instrucciones:", instrucciones, height=150)

# Función para agregar receta a la base de datos
def agregar_receta():
    st.title("Agregar Receta")
    nombre = st.text_input("Nombre de la receta")
    ingredientes = st.text_area("Ingredientes")
    instrucciones = st.text_area("Instrucciones")
    if st.button("Agregar Receta"):
        agregar_receta_db(nombre, ingredientes, instrucciones)
        st.success("Receta agregada exitosamente!")

# Función para manejar inventario
def Inventario():
    st.title("Inventario")
    cursor.execute("SELECT * FROM inventario_BP")
    inventario_data = cursor.fetchall()
    df_inventario = pd.DataFrame(inventario_data, columns=["ID Ingrediente", "Ingrediente", "Cantidad", "Unidad"])
    st.table(df_inventario)

# Visualización de datos
def visualizacion_datos():
    st.title("Visualización de Datos")
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
def agregar_receta_db(nombre, ingredientes, instrucciones):
    cursor.execute('''INSERT INTO recetas_BP (nombre_receta, ingredientes, instrucciones) VALUES (?, ?, ?)''', (nombre, ingredientes, instrucciones))
    conn.commit()

# Funciones para obtener datos de la base de datos
def obtener_recetas():
    cursor.execute("SELECT * FROM recetas_BP")
    return cursor.fetchall()

def obtener_ingredientes_por_receta(conn, id_receta):
    query = '''
    SELECT ir.id_ingrediente, ir.cantidad, ir.unidad_medida
    FROM ingre_receta_BP AS ir
    JOIN ingredientes_BP AS i ON ir.id_ingrediente = i.id_ingredientes
    WHERE ir.id_receta = ?
    '''
    return pd.read_sql_query(query, conn, params=(id_receta,))

def obtener_instrucciones(conn, id_receta):
    query = "SELECT instrucciones FROM recetas_BP WHERE id_receta = ?"
    pasos = pd.read_sql_query(query, conn, params=(id_receta,))
    instrucciones = "\n".join(pasos["instrucciones"])
    return instrucciones if instrucciones else "Instrucciones no disponibles"

# Navegación entre páginas
if selection == "Inicio":
    home()
elif selection == "Consultar recetas":
    consultar_recetas(conn)
elif selection == "Agregar receta":
    agregar_receta()
elif selection == "Inventario":
    Inventario()
elif selection == "Registro de datos":
    visualizacion_datos()

# Cerrar la conexión a la base de datos
conn.close()
