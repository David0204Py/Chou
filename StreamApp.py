import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import time

# Funcion para cargar el archivo JavaScript
def load_js(file_name):
    with open(file_name) as f:
        st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)

# Llamando la función para cargar el JS
load_js('static/script.js')

# Función para cargar el archivo CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Llamando la funcion para cargar el CSS
load_css('static/styles.css')

# Conectando a la base de datos
conn = sqlite3.connect('base_datos.db')
cursor = conn.cursor()

# Función para mostrar el logotipo con animación
def mostrar_logotipos():
    # Mostrar el primer logotipo
    logotipo1 = st.empty()
    logotipo1.image("Icono_020_PNG_BP.png", use_column_width=True)
    # Esperar un momento
    time.sleep(2)  # Tiempo que se muestra el primer logotipo
    # Animación de recogida hacia el centro (simulada con un tiempo de espera)
    for i in range(6):
        logotipo1.image("Icono_020_PNG_BP.png", use_column_width=True)
        time.sleep(0.1)  # Simula la recogida (puedes ajustar el tiempo)
    # Limpiar el primer logotipo
    logotipo1.empty()
    # Mostrar el segundo logotipo
    logotipo2 = st.empty()
    logotipo2.image("Icono_030_PNG_BP.png", use_column_width=True)
# Llamar a la función para mostrar los logotipos
mostrar_logotipos()

# Sistema de navegación
menu = ["Inicio", "Consultar recetas", "Agregar receta", "Inventario", "Registro de datos"]
selection = st.sidebar.selectbox("Bienvenido Chou. Usa el menú para navegar.", menu)

# Funciónes para cada página
def home():
    # Mensaje principal
    st.markdown("<h2 style='text-align: center;'>Arte dulce, para saborear y admirar.</h2>", unsafe_allow_html=True)
    st.title("Bienvenido a Chou")
    st.markdown("<p style='text-align: center;'>En Chou, creamos repostería francesa artesanal, combinando técnica y creatividad. Ofrecemos tanto dulces como salados, todos con un toque artístico que convierte cada pieza en una pequeña obra maestra.</p>", unsafe_allow_html=True)

def consultar_recetas(conn):
    st.title("Consultar Recetas")
    
    receta_nombre = st.text_input("Buscar receta por nombre")
    
    # Consultar las recetas (sin la columna de índice)
    query = "SELECT id_receta, nombre_receta, pagina FROM recetas_BP WHERE nombre_receta LIKE ?"
    df_recetas = pd.read_sql_query(query, conn, params=(f"%{receta_nombre}%",))
    
    if df_recetas.empty:
        st.warning("No se encontraron recetas que coincidan con tu búsqueda.")
        return
    
    st.table(df_recetas[["nombre_receta", "pagina"]])  # Tabla sin columna de índice

    # Selección de una receta
    receta_seleccionada = st.selectbox("Selecciona una receta", df_recetas["id_receta"].tolist())
    
    if receta_seleccionada:
        # Obtener ingredientes de la receta seleccionada
        df_ingredientes = obtener_ingredientes_por_receta(conn, receta_seleccionada)
        cantidad_base = st.number_input("Ajustar cantidad de base", min_value=1, value=1, key="cantidad_base")

        # Ajustar las cantidades
        df_ingredientes["Cantidad Ajustada"] = df_ingredientes["cantidad"] * cantidad_base
        st.table(df_ingredientes[["id_ingrediente", "Cantidad Ajustada", "unidad_medida"]])

        # Mostrar las instrucciones formateadas
        instrucciones = obtener_instrucciones(conn, receta_seleccionada)
        st.text_area("Instrucciones:", instrucciones, height=150)    
    if receta_seleccionada:
        # Obtener ingredientes de la receta seleccionada
        df_ingredientes = obtener_ingredientes_por_receta(conn, receta_seleccionada)
        cantidad_base = st.number_input("Ajustar cantidad de base", min_value=1, value=1)
        
        # Ajustar las cantidades
        df_ingredientes["Cantidad Ajustada"] = df_ingredientes["cantidad"] * cantidad_base
        st.table(df_ingredientes[["id_ingredients", "Cantidad Ajustada", "unidad_medida"]])

        # Mostrar las instrucciones formateadas
        instrucciones = obtener_instrucciones(conn, receta_seleccionada)
        st.text_area("Instrucciones:", instrucciones, height=150)

def agregar_receta():
    st.title("Agregar Receta")
    # Formulario para agregar nuevas recetas
    nombre = st.text_input("Nombre de la receta")
    ingredientes = st.text_area("Ingredientes")
    instrucciones = st.text_area("Instrucciones")
    if st.button("Agregar Receta"):
        agregar_receta_db(nombre, ingredientes, instrucciones)
        st.success("Receta agregada exitosamente!")

def Inventario():
    st.title("Inventario")
    st.write("Aquí podrás modificar el inventario de ingredientes.")
# Mostrar inventario
    cursor.execute("SELECT * FROM inventario_BP")
    inventario_data = cursor.fetchall()
    df_inventario = pd.DataFrame(inventario_data, columns=["ID Ingrediente", "Ingrediente", "Cantidad", "Unidad"])
    st.table(df_inventario)

def visualizacion_datos():
    st.title("Visualización de Datos 1")
    # Consultar datos desde la base de datos y mostrar gráficos interactivos
    recetas = obtener_recetas()
    nombres = [receta[1] for receta in recetas]
    # Gráfico de cantidad de recetas
    fig1 = plt.figure()
    plt.barh(nombres, [1] * len(nombres))
    plt.xlabel('Cantidad de recetas')
    plt.title('Visualización de Recetas')
    st.pyplot(fig1)
    # Gráfico de costo de ingredientes
    cursor.execute("SELECT nombre_ingrediente, precio FROM ingredientes_BP")
    ingredientes_data = cursor.fetchall()
    df_ingredientes = pd.DataFrame(ingredientes_data, columns=["Ingrediente", "Precio"])
    fig2 = px.bar(df_ingredientes, x="Ingrediente", y="Precio", title="Costo de Ingredientes")
    st.plotly_chart(fig2)

# Función para agregar recetas a la base de datos
def agregar_receta_db(nombre, ingredientes, instrucciones):
    cursor.execute('''
        INSERT INTO recetas_BP (nombre, ingredientes, instrucciones)
        VALUES (?, ?, ?)
    ''', (nombre, ingredientes, instrucciones))
    conn.commit()

# Función para obtener todas las recetas
def obtener_recetas():
    cursor.execute("SELECT * FROM recetas_BP")
    return cursor.fetchall()

def obtener_ingredientes_por_receta(conn, id_receta):
    query = '''
    SELECT ir.id_ingrediente, ir.cantidad, ir.unidad_medida
    FROM ingre_recetas_BP AS ir
    JOIN ingredientes_BP AS i ON ir.id_ingrediente = i.id_ingredientes
    WHERE ir.id_receta = ?
    '''
    return pd.read_sql_query(query, conn, params=(id_receta,))

def obtener_instrucciones(conn, id_receta):
    query = '''
    SELECT id_receta, instrucciones
    FROM recetas_BP
    WHERE id_receta = ?
    ORDER BY id_receta
    '''
    pasos = pd.read_sql_query(query, conn, params=(id_receta,))
    # Convertir los pasos a un solo string con salto de línea
    instrucciones = "\n".join(f"{row['id_receta']}. {row['instrucciones']}" for _, row in pasos.iterrows())
    return instrucciones if instrucciones else "Instrucciones no disponibles"


# Lógica para navegar entre páginas
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

# Cerrando la conexión a la base de datos
conn.close()

#--------------------------------------------

