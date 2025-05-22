import streamlit as st
# Set page configuration
st.set_page_config(
    layout="wide",
    page_title="MSM Buscador de Productos",
    page_icon="🔍",
    initial_sidebar_state="collapsed")

import pandas as pd
import os
import re
from pathlib import Path
import logging
import time
import traceback
import search
from PIL import Image
import gdown
import warnings
import requests
import base64
from logger import log_search

warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


logo = Image.open('img/logo.jpeg')
# Calcula el ancho proporcional para mantener la relación de aspecto
height_ratio = 110 / float(logo.size[1])
new_width = int(float(logo.size[0]) * height_ratio)
# Redimensiona la imagen
resized_logo = logo.resize((new_width, 110), Image.LANCZOS)
col1, col2 = st.columns([1.65, 3])
with col1:
    st.image(resized_logo)
with col2:
    st.markdown("<h1>MSM Buscador de productos</h1>", unsafe_allow_html=True)


# Function to initialize index and model - cache this to avoid reloading
@st.cache_resource
def initialize_search_resources(file_path):
    """Initialize search resources like model and index with caching to avoid repeated loading"""
    # Enlace de Google Drive
    url = st.secrets["url"]["data"]

    # Descargar el archivo CSV de Google Drive
    output = 'data.csv'  # Ruta donde quieres guardar el archivo descargado
    gdown.download(url, output, quiet=False)
    df = pd.read_csv(output)

    return df


# URL del archivo de fuente
font_url = "https://github.com/jondot/dotfiles/raw/master/.fonts/calibri.ttf"

# Función para descargar y guardar el archivo
def download_font(url, local_path="calibri.ttf"):
    if not os.path.exists(local_path):
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(response.content)
            print(f"Fuente descargada y guardada en {local_path}")
        else:
            print(f"Error al descargar la fuente: {response.status_code}")
            return None
    return local_path

# Función para convertir el archivo de fuente a base64
def get_font_base64(file_path):
    with open(file_path, "rb") as f:
        font_bytes = f.read()
    return base64.b64encode(font_bytes).decode()


# Descargar y obtener la fuente en base64
font_path = download_font(font_url)
if font_path:
    font_base64 = get_font_base64(font_path)
    
    # Aplicar el CSS con @font-face
    st.markdown(f"""
    <style>
        @font-face {{
            font-family: 'Calibri';
            src: url(data:font/truetype;base64,{font_base64}) format('truetype');
            font-weight: normal;
            font-style: normal;
        }}
        
        .stDataEditor {{
            font-family: 'Calibri', sans-serif !important;
            font-size: 11px !important;
        }}
        .stDataEditor div[data-testid="stDataEditorCell"] {{
            font-family: 'Calibri', sans-serif !important;
            font-size: 11px !important;
        }}
    </style>
    """, unsafe_allow_html=True)




# CSS más refinado para una apariencia más sutil y elegante
css = """
<style>
    /* Estilos generales para inputs y selectbox */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        border: 0.3px solid rgba(0, 0, 0, 0.15) !important;
        border-radius: 4px !important;
        box-shadow: none !important;
        transition: border 0.2s ease !important;
    }
    
    /* Efecto hover */
    .stTextInput > div > div > input:hover,
    .stSelectbox > div > div > div:hover {
        border: 0.3px solid rgba(0, 0, 0, 0.25) !important;
    }
    
    /* Efecto focus */
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border: 0.3px solid rgba(0, 0, 0, 0.2) !important;
        box-shadow: 0 0 2px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Estilo para los radio buttons */
    .stRadio > div {
        padding: 0.2rem 0 !important;
    }
    
    /* Estilo para el checkbox */
    .stCheckbox > div > div > label {
        font-size: 0.9rem !important;
    }
    
    /* Botones */
    .stButton > button {
        border: 0.3px solid rgba(0, 0, 0, 0.15) !important;
        border-radius: 4px !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
</style>
"""

# Aplicar el CSS personalizado
st.markdown(css, unsafe_allow_html=True)




# Function to highlight search term in text
def highlight_text(text, search_term):
    if not isinstance(text, str) or not isinstance(search_term, str) or search_term == "":
        return text
    
    # Escape special regex characters in search term
    escaped_search = re.escape(search_term)
    
    # Create a pattern that matches the search term case-insensitively
    pattern = re.compile(f"({escaped_search})", re.IGNORECASE)
    
    # Replace matches with highlighted version
    highlighted = pattern.sub(r'<span class="highlight">\1</span>', text)
    
    return highlighted

# Main application
def main():
    # Header with logo and title
    #st.markdown("""
    #<div class="header-container">
    #    <h1>MSM Buscador de Productos Avanzado</h1>
    #</div>
    #""", unsafe_allow_html=True)
    # Verificar si el usuario está autenticado
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        _, col, _ = st.columns([2, 1, 2])
        with col:
          # Si no está autenticado, mostrar el formulario de login
          st.markdown("""
                  <h3>Iniciar Sesión</h3>
              """, unsafe_allow_html=True)
          
          # Obtener credenciales encriptadas desde secrets.toml
          users = st.secrets["credentials"]
      
          # Crear formulario de login
          username = st.text_input("Usuario")
          password = st.text_input("Contraseña", type="password")
          # Crear botón de login
          if st.button("Iniciar sesión"):
              if username in users and password == users[username]:
                  st.success(f"✅ Bienvenido, {username}!")
                  st.session_state["authenticated"] = True  # Guardar sesión
                  st.session_state["username"] = username
                  st.rerun()  # Recargar la app para mostrar el contenido
              else:
                  st.error("❌ Usuario o contraseña incorrectos")
    else:
     
      # Initialize session state variables
      nsearch_boxes = 4
      
      # Initialize all session state variables first
      for i in range(nsearch_boxes):
          if f'search_{i}' not in st.session_state:
              st.session_state[f'search_{i}'] = ''
          if f'logical_{i}' not in st.session_state:
              st.session_state[f'logical_{i}'] = ''
          if f'contains_{i}' not in st.session_state:
              st.session_state[f'contains_{i}'] = ''
    
      if 'skusearch' not in st.session_state:
          st.session_state['skusearch'] = ''
      
      # Determine file path
      file_path = Path("Datos/datos_app.csv")
      
      # Load resources - CACHED to prevent reloading every time
      df = initialize_search_resources(file_path)

      # Inicializar variables del estado para búsqueda y resultados
      if 'search_results' not in st.session_state:
          st.session_state['search_results'] = None
      if 'search_performed' not in st.session_state:
          st.session_state['search_performed'] = False
      if 'all_providers' not in st.session_state:
          st.session_state['all_providers'] = ['Todos'] + sorted(list(df['Proveedor'].unique()))
      if 'result_providers' not in st.session_state:
          st.session_state['result_providers'] = ['Todos']
      if 'post_search_provider' not in st.session_state:
          st.session_state['post_search_provider'] = 'Todos'

      # Inicializar variable para almacenar filas seleccionadas
      if 'selected_rows' not in st.session_state:
          st.session_state['selected_rows'] = pd.DataFrame()

      # Set up search columns
      search_cols = st.columns([2.5, 3, 3, 3])
      
      operadores_logicos = ["Y", "O"]
      operador_contains = ["Contiene", "No contiene"]
      
      # Create empty subcols dict
      subcols = {i: [] for i in range(nsearch_boxes)}
      
    # Process each search box
      for i in range(nsearch_boxes):
          with search_cols[i % len(search_cols)]:  # Ensure we don't go out of bounds
              # Create subcols based on search box index
              if i == 0:
                  subcols[i] = st.columns([0.7, 0.5])
              else:
                  subcols[i] = st.columns([0.25, 0.9, 0.7])
              
              # Handle first column in subcols
              with subcols[i][0]:
                  if i >= 1:
                      # Logic operator for boxes after the first
                      if st.session_state[f'search_{i-1}'] != '':
                          logica = st.radio("", operadores_logicos, key=f'Logica{i}', index=0)
                          st.session_state[f'logical_{i}'] = logica
                      else:
                          #logica = st.selectbox("", operadores_logicos, key=f'Logica{i}', index=0, disabled=True)
                          st.session_state[f'logical_{i}'] = ''
                  else:
                      # Contains operator for the first box
                      contains_or_not = st.radio("", operador_contains, key=f'Contains{i}')
                      st.session_state[f'contains_{i}'] = contains_or_not
              
              # Handle second column in subcols
              with subcols[i][1]:
                  if i == 0:
                      # Search term for first box
                      if st.session_state[f'contains_{i}'] != '':                        
                          subterm = st.text_input("", value=st.session_state[f'search_{i}'], key=f'SearchTerm{i}')
                          st.session_state[f'search_{i}'] = subterm
                      else:
                          subterm = st.text_input("", value="", key=f'SearchTerm{i}_disabled', disabled=True)
                          st.session_state[f'search_{i}'] = ''
                  else:
                      # Contains operator for boxes after the first
                      if st.session_state[f'logical_{i}'] != '':
                          contains_or_not = st.radio("", operador_contains, key=f'Contains{i}')
                          st.session_state[f'contains_{i}'] = contains_or_not
                      else:
                          #contains_or_not = st.selectbox("", operador_contains[0:1], key=f'Contains{i}', disabled=True)
                          st.session_state[f'contains_{i}'] = ''
              
              # Handle third column in subcols (only for boxes after the first)
              if i >= 1 and len(subcols[i]) > 2:
                  with subcols[i][2]:
                      if st.session_state[f'logical_{i}'] != '' and st.session_state[f'contains_{i}'] != '':
                          subterm = st.text_input("", value=st.session_state[f'search_{i}'], key=f'SearchTerm{i}')
                          st.session_state[f'search_{i}'] = subterm
                      else:
                          #subterm = st.text_input("", value="", key=f'SearchTerm{i}_disabled', disabled=True)
                          st.session_state[f'search_{i}'] = ''

          
      col, colr = st.columns([1.5, 1])
      with col:
          subc = st.columns([1.5, 2, 1.8, 3])

          with subc[0]:              
            considerar_ofertas = ["No", "Sí"]
            seleccion_ofertas = st.radio("Considerar ofertas:", considerar_ofertas, horizontal=True)
          with subc[1]:
            considerar_descripcion = st.checkbox('Buscar sólo en "Nombre Producto"')
          
          with subc[-1]:
            incluir_excluir = ["Incluir", "Excluir"]
            seleccion_provs = st.radio("Filtrar proveedor:", incluir_excluir, horizontal=True, label_visibility='collapsed')
            provs = sorted(list(df['Proveedor'].unique()))
            buscar_en_prov = st.multiselect('', provs, placeholder='Proveedores', label_visibility='collapsed')
          with subc[2]:
            mostrar_stock = st.radio("Mostrar productos sin stock:", considerar_ofertas, horizontal=True)


      with colr:
          subc = st.columns([1.5, 1.5, 1, 1, 2, 0.1, 0.9])

          with subc[-3]:
            buscar_sku = st.text_input(placeholder="Buscar SKU", key='skutext', label='', label_visibility='collapsed', value=st.session_state['skusearch'])
            st.session_state['skusearch'] = buscar_sku
          with subc[-2]:
            boton_sku = st.button("🔍")


      col1, col2 = st.columns([1, 1])
      with col1:
          #subc = st.columns([1.5, 1.5, 1.5, 0.1, 0.9, 1, 1])
          subc = st.columns([1.5, 1.5, 1.5, 2, 0.1, 0.9])
          with subc[0]:              
            # Search button
            search_clicked = st.button("🔍 Buscar")

          with subc[1]:
            if st.button("Limpiar", key="limpiar"):
                # Clear search state variables
                st.session_state[f'search_0'] = ''
                st.session_state[f'logical_0'] = ''
                st.session_state[f'contains_0'] = ''
                st.session_state[f'search_1'] = ''
                st.session_state[f'logical_1'] = ''
                st.session_state[f'contains_1'] = ''
                st.session_state[f'search_2'] = ''
                st.session_state[f'logical_2'] = ''
                st.session_state[f'contains_2'] = ''
                st.session_state[f'search_3'] = ''
                st.session_state[f'logical_3'] = ''
                st.session_state[f'contains_3'] = ''
                
                # Clear search results
                st.session_state['search_results'] = None
                st.session_state['search_performed'] = False
                st.session_state['result_providers'] = ['Todos']
                st.session_state['post_search_provider'] = 'Todos'
                
                # Clear SKU search
                st.session_state['skusearch'] = ''
                
                # Force a rerun to refresh all widgets with cleared values
                st.rerun()
          with subc[2]:
              if st.session_state['username'] in st.secrets["admins"]:
                  ver_datos = st.button("Reporte")

                  if ver_datos:
                      st.switch_page("report.py")
                              
              
      with col2:
          subc = st.columns([1, 1, 1, 1, 1, 0.25, 0.25])

      if boton_sku:
        try:
          sku_results = df[df['Codigo Prov'] == buscar_sku]
          st.data_editor(sku_results.reset_index(drop=True).style.format({
                              "Precio MSM": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) and x > 0 else "", 
                              "Precio Oferta": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) and x > 0 else "", 
                              "Precio Lista": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) and x > 0 else "",
                              'T. Entrega': "{:.0f}",
                              "Stock": lambda x: f"{float(x):.0f}" if pd.notnull(x) and str(x).strip() and str(x).replace('.', '', 1).isdigit() else x
                          }), 
                          height=690, 
                          use_container_width=True, 
                          column_config={"Codigo Prov": st.column_config.LinkColumn("Codigo Prov", width=110), "Descripcion": st.column_config.TextColumn("Descripcion", width=420), "Stock": st.column_config.TextColumn("Stock", width=100),
                          "Comentario": st.column_config.TextColumn("Comentario", width=200), "Url": st.column_config.LinkColumn("Url", width=800)},
                          disabled=True)
        except:
            pass
      # Display results
      #if search_clicked or search_term:
      if search_clicked:
          try:
              with st.spinner("Buscando productos..."):

                  # Recopilar parámetros de búsqueda para logging
                  search_params = {}
                  for i in range(nsearch_boxes):
                      search_params[f'search_{i}'] = st.session_state.get(f'search_{i}', '')
                      search_params[f'logical_{i}'] = st.session_state.get(f'logical_{i}', '')
                      search_params[f'contains_{i}'] = st.session_state.get(f'contains_{i}', '')


                  # Realizar la búsqueda
                  search_results = search.key_search(nsearch_boxes, st.session_state, df, seleccion_ofertas, considerar_descripcion, buscar_en_prov, seleccion_provs, mostrar_stock)

                  # Guardar resultados en el estado de la sesión
                  st.session_state['search_results'] = search_results
                  st.session_state['search_performed'] = True
                  st.session_state['current_page'] = 1
                  # Actualizar la lista de proveedores disponibles en los resultados
                  if isinstance(search_results, pd.DataFrame) and not search_results.empty:
                      if 'Descripcion' in search_results.columns:
                        search_results = search_results.rename(columns={'Descripcion': 'Nombre Producto'})

                                 # Registrar la búsqueda
                  try:
                      username = st.session_state.get("username", "usuario_desconocido")
                      if username not in st.secrets["admins"]:
                        log_search(
                            username=username,
                            search_params=search_params,
                            considerar_ofertas=seleccion_ofertas,
                            proveedores=buscar_en_prov
                        )
                  except Exception as e:
                      logger.error(f"Error al registrar la búsqueda: {str(e)}")
                      logger.error(traceback.format_exc())
                  
          except Exception as e:
            st.error(f"Error al realizar la búsqueda: {str(e)}")
            logger.error(f"Search error: {e}")
            logger.error(traceback.format_exc())
      
      # Mostrar y filtrar resultados si ya se realizó una búsqueda
      if st.session_state['search_performed'] and st.session_state['search_results'] is not None:
          filtered_df = st.session_state['search_results']
          rows_per_page = 50
          total_pages = max(1, (len(filtered_df) + rows_per_page - 1) // rows_per_page)

          # Calcular índices para la página actual
          start_idx = (st.session_state.current_page - 1) * rows_per_page
          end_idx = min(start_idx + rows_per_page, len(filtered_df))
          results_df = st.session_state['search_results'].iloc[start_idx:end_idx].copy()          
          
          filtered_results = results_df
          # Mostrar información de resultados
          if isinstance(filtered_results, pd.DataFrame):
              
              with subc[-3]:
                  st.write(f"Página {st.session_state.current_page}/{total_pages}")
              with subc[-2]:
                  if st.button("←") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()
              with subc[-1]:
                  if st.button("→") and st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1
                    st.rerun()                    

                            
              if not filtered_results.empty:
                               
                st.data_editor(
                    filtered_results.reset_index(drop=True).style.format({
                        "Precio MSM": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) and x > 0 else "", 
                        "Precio Oferta": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) and x > 0 else "", 
                        "Precio Lista": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) and x > 0 else "",
                        'T. Entrega': "{:.0f}",
                        "Stock": lambda x: f"{float(x):.0f}" if pd.notnull(x) and str(x).strip() and str(x).replace('.', '', 1).isdigit() else x
                    }), 
                    height=690, 
                    use_container_width=True, 
                    column_config={"Codigo Prov": st.column_config.LinkColumn("Codigo Prov", width=110), "Descripcion": st.column_config.TextColumn("Descripcion", width=420), "Stock": st.column_config.TextColumn("Stock", width=100),
                    "Comentario": st.column_config.TextColumn("Comentario", width=200), "Url": st.column_config.LinkColumn("Url", width=800)},
                    disabled=True
                )

                col1, col2 = st.columns([1, 1])
                with col2:
                    subc = st.columns([1, 1, 1, 1, 1, 0.25, 0.25])

                filtered_df = st.session_state['search_results']
                rows_per_page = 50
                total_pages = max(1, (len(filtered_df) + rows_per_page - 1) // rows_per_page)

                # Calcular índices para la página actual
                start_idx = (st.session_state.current_page - 1) * rows_per_page
                end_idx = min(start_idx + rows_per_page, len(filtered_df))
                results_df = st.session_state['search_results'].iloc[start_idx:end_idx].copy()          
                
                filtered_results = results_df
                # Mostrar información de resultados
                if isinstance(filtered_results, pd.DataFrame):
                    
                    with subc[-3]:
                        st.write(f"Página {st.session_state.current_page}/{total_pages}")
                    with subc[-2]:
                        if st.button("←", key="left2") and st.session_state.current_page > 1:
                          st.session_state.current_page -= 1
                          st.rerun()
                    with subc[-1]:
                        if st.button("→", key="right2") and st.session_state.current_page < total_pages:
                          st.session_state.current_page += 1
                          st.rerun()      

              else:
                  st.info("No se encontraron resultados para el filtro seleccionado.")

          else:
              st.info("No se encontraron resultados para la búsqueda.")

   
main()
