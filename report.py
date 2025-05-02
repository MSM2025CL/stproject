import streamlit as st
from logger import get_search_logs
import pandas as pd 
import seaborn as sns
from matplotlib import pyplot as plt 
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta



def ultimas_semanas(num_semanas=10):
    # Nombres de los meses en español
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()
    
    # Encontrar el lunes de la semana actual
    inicio_semana_actual = fecha_actual - timedelta(days=fecha_actual.weekday())
    
    # Lista para almacenar los rangos de fechas
    semanas = []
    
    # Generar las últimas 'num_semanas' semanas (incluida la actual)
    for i in range(num_semanas):
        # Calcular el inicio de la semana (lunes)
        inicio_semana = inicio_semana_actual - timedelta(weeks=i)
        
        # Calcular el fin de la semana (domingo)
        fin_semana = inicio_semana + timedelta(days=6)
        
        # Formatear las fechas como 'DIA MES AÑO'
        inicio_str = f"{inicio_semana.day}/{inicio_semana.month}/{inicio_semana.year}"
        fin_str = f"{fin_semana.day}/{fin_semana.month}/{fin_semana.year}"
        
        # Crear el string en formato 'fecha inicio - fecha final'
        rango_semana = f'{inicio_str} - {fin_str}'
        
        # Añadir a la lista
        semanas.append(rango_semana)
    
    return semanas

def inicio_semana(fecha):
    # El método weekday() devuelve 0 para lunes, 1 para martes, etc.
    dias_desde_inicio = fecha.weekday()
    
    # Restar los días necesarios para llegar al inicio de la semana (lunes)
    fecha_inicio = fecha - timedelta(days=dias_desde_inicio)
    
    return fecha_inicio

if "authenticated" in st.session_state and st.session_state["authenticated"] and st.session_state["username"] in st.secrets["admins"]:
  st.title("Datos de uso")

  # Primero debemos pullear los datos desde google sheets
  # Para esto usamos la función de logger.py

  datos_uso = get_search_logs()
  datos_uso = datos_uso[~datos_uso['username'].isin(st.secrets["admins"])]
  

  tipos_reporte = ['Búsquedas totales (todos los usuarios)', 'Búsquedas diarias por usuario']

  meses = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}


  ## PANEL DE CONFIGURACIÓN DE REPORTE

  col_l, col_r = st.columns([1, 1])

  # SELECCION DE TIPO DE REPORTE Y PERIODO
  with col_l:
    subcols_left = st.columns([1, 1])
    with subcols_left[0]:
      eleccion_reporte = st.selectbox("Selecciona un reporte:", tipos_reporte)
    with subcols_left[1]:
      # Elegir un periodo
      periodo = st.selectbox("Selecciona un periodo:", ['Mensual', 'Semanal', 'Diario', 'Personalizado'])

  # PANEL SEGUN ELECCIONES
  # BUSQUEDAS POR USUARIO
  if 'Búsquedas' in eleccion_reporte:
    if periodo == 'Mensual':
      with col_r:
        subcols_right = st.columns([1, 1])
        with subcols_right[0]:
          # Elegir mes
          busqueda_mensual_mes = st.selectbox("Selecciona un mes:", meses)
        with subcols_right[1]:
          # Elegir año
          busqueda_mensual_ano = st.selectbox("Selecciona un año:", [str(i) for i in range(2025, 2026)])

    elif periodo == 'Semanal':
      with col_r:
        subcols_right = st.columns([1, 1])
        with subcols_right[0]:
          # Elegir alguna semana de las semanas anteriores dentro del presente año
          # Formato: Fecha inicio semana - Fecha fin semana
          semanas_anteriores = ultimas_semanas(5)
          busqueda_semanal = st.selectbox("Selecciona una semana:", semanas_anteriores)
    
    elif periodo == 'Diario':
      with col_r:
        subcols_right = st.columns([1, 1])
        with subcols_right[0]:
          busqueda_diaria = st.date_input("Selecciona una fecha:", value=datetime.today(), format="DD/MM/YYYY" )

    elif periodo == 'Personalizado':
      with col_r:
        subcols_right = st.columns([1, 1])
        with subcols_right[0]:
          fecha_inicio = st.date_input("Desde:", value=datetime.today(), format="DD/MM/YYYY" )
        with subcols_right[1]:  
          fecha_fin = st.date_input("Hasta:", value=datetime.today(), format="DD/MM/YYYY" )
        
        fecha_inicio = pd.Timestamp(fecha_inicio)
        fecha_fin = pd.Timestamp(fecha_fin)
    
    if 'todos' not in eleccion_reporte:
      col_left, col_right = st.columns([1, 1])
      with col_left:
          subcols_left = st.columns([1, 1])
          with subcols_left[0]:
            # Seleccionar usuario
            busqueda_usuario = st.selectbox("Selecciona un usuario:", sorted(list(datos_uso['username'].unique())))

  # Funciones para generar los diferentes gráficos

  def generar_grafico_mensual(datos, mes, ano, tipo_reporte):
      # Convertir el nombre del mes a su número
      meses = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 
              'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}
      
      mes_num = meses[mes]
      
      # Filtrar datos por el mes y año seleccionados
      datos['fecha'] = pd.to_datetime(datos['timestamp'])
      filtrados = datos[
          (datos['fecha'].dt.month == mes_num) & 
          (datos['fecha'].dt.year == int(ano))
      ]
      
      if filtrados.empty:
          st.warning(f"No hay datos para {mes} de {ano}")
          return None
      
      if 'usuario' in tipo_reporte.lower() and 'todos' in tipo_reporte.lower():
          # Agrupar por usuario y contar las búsquedas
          df_agrupado = filtrados.groupby('username').size().reset_index(name='búsquedas')
          # Ordenar el dataframe de mayor a menor según la columna 'búsquedas'
          df_agrupado = df_agrupado.sort_values(by='búsquedas', ascending=False)
          fig = px.bar(
              df_agrupado, 
              x='username', 
              y='búsquedas',
              title=f'Búsquedas por usuario en {mes} de {ano}',
              labels={'username': 'Usuario', 'búsquedas': 'Número de búsquedas'}
          )

          # Crear rangos personalizados para los yticks basados en los datos reales
          max_busquedas = df_agrupado['búsquedas'].max()

          # Crear marcas personalizadas que sean fáciles de leer
          # Para este caso específico con valores que llegan a ~600
          ticks = [50*i for i in range(20)]
          # Filtrar solo los ticks que son relevantes para nuestros datos
          ticks = [t for t in ticks if t <= max_busquedas + 50]

          # Actualizar la configuración del gráfico
          fig.update_layout(
              yaxis=dict(
                  tickmode='array',
                  tickvals=ticks,
                  range=[0, max_busquedas * 1.1],  # Dar un poco de espacio arriba
                  title=dict(
                      text="<b>Total de búsquedas</b>",
                      font=dict(size=20)
                  ),
                  gridcolor='lightgray',  # Líneas de cuadrícula más sutiles
                  # Garantizar que las líneas de cuadrícula aparezcan en cada marca
                  showgrid=True
              ),
              xaxis=dict(
                  title=dict(
                      text="<b>Usuario</b>",
                      font=dict(size=20)
                  )
              ),
              # Mejorar el diseño general
              plot_bgcolor='white',  # Fondo blanco para mejor legibilidad
              margin=dict(t=50, r=20, b=100, l=50),  # Márgenes para evitar cortes
          )

          # Agregar etiquetas de valor encima de cada barra para facilitar la lectura
          fig.update_traces(
              texttemplate='%{y}',  # Mostrar el valor exacto
              textposition='outside',  # Colocar el texto fuera de la barra
              textfont=dict(size=14)  # Tamaño de fuente adecuado
          )

          # Opcional: Agregar una línea de promedio para dar contexto
          promedio = df_agrupado['búsquedas'].mean()
          fig.add_hline(
              y=promedio, 
              line_dash="dash", 
              line_color="red",
              annotation_text=f"Promedio: {promedio:.1f}",
              annotation_position="top right",
              annotation_font=dict(
              color="red",  # Aquí se define el color rojo para el texto
              size=14
          )
          )


      elif 'usuario' in tipo_reporte.lower() and 'todos' not in tipo_reporte.lower():
          # Seleccionar el usuario "busqueda_usuario"
          filtrados = filtrados[filtrados['username'] == busqueda_usuario]
          # Agrupar por día y contar las búsquedas
          filtrados['día'] = filtrados['fecha'].dt.day
          df_agrupado = filtrados.groupby('día').size().reset_index(name='búsquedas')
          fig = px.bar(
              df_agrupado, 
              x='día', 
              y='búsquedas',
              title=f'Búsquedas totales diarias en {mes} de {ano}',
              labels={'día': 'Día del mes', 'búsquedas': 'Número de búsquedas'}
          )

          # Crear rangos personalizados para los yticks basados en los datos reales
          max_busquedas = df_agrupado['búsquedas'].max()

          # Crear marcas personalizadas que sean fáciles de leer
          # Para este caso específico con valores que llegan a ~600
          ticks = [10*i for i in range(20)]
          # Filtrar solo los ticks que son relevantes para nuestros datos
          ticks = [t for t in ticks if t <= max_busquedas + 50]

          # Actualizar la configuración del gráfico
          fig.update_layout(
              yaxis=dict(
                  tickmode='array',
                  tickvals=ticks,
                  range=[0, max_busquedas * 1.1],  # Dar un poco de espacio arriba
                  title=dict(
                      text="<b>Número de búsquedas</b>",
                      font=dict(size=20)
                  ),
                  gridcolor='lightgray',  # Líneas de cuadrícula más sutiles
                  # Garantizar que las líneas de cuadrícula aparezcan en cada marca
                  showgrid=True
              ),
              xaxis=dict(dtick=1, tickmode='linear',
                  title=dict(
                      text="<b>Día del mes</b>",
                      font=dict(size=20)  
                  )
              ),
              # Mejorar el diseño general
              plot_bgcolor='white',  # Fondo blanco para mejor legibilidad
              margin=dict(t=50, r=20, b=100, l=50),  # Márgenes para evitar cortes
          )

          # Agregar etiquetas de valor encima de cada barra para facilitar la lectura
          fig.update_traces(
              texttemplate='%{y}',  # Mostrar el valor exacto
              textposition='outside',  # Colocar el texto fuera de la barra
              textfont=dict(size=14)  # Tamaño de fuente adecuado
          )

          # Opcional: Agregar una línea de promedio para dar contexto
          promedio = df_agrupado['búsquedas'].mean()
          fig.add_hline(
              y=promedio, 
              line_dash="dash", 
              line_color="red",
              annotation_text=f"Promedio: {promedio:.1f}",
              annotation_position="top right",
              annotation_font=dict(
              color="red",  # Aquí se define el color rojo para el texto
              size=14
          )
          )
      return fig
          

  def generar_grafico_semanal(datos, semana, tipo_reporte):
      # Extraer fechas de inicio y fin de la semana
      inicio_str, fin_str = semana.split(' - ')
      inicio = datetime.strptime(inicio_str, '%d/%m/%Y')
      fin = datetime.strptime(fin_str, '%d/%m/%Y')
      
      # Filtrar datos por la semana seleccionada
      datos['fecha'] = pd.to_datetime(datos['timestamp'])
      filtrados = datos[
          (datos['fecha'] >= inicio) & 
          (datos['fecha'] <= fin)
      ]
      
      if filtrados.empty:
          st.warning(f"No hay datos para la semana del {inicio_str} al {fin_str}")
          return None
      
      if 'usuario' in tipo_reporte.lower() and 'todos' in tipo_reporte.lower():
          # Agrupar por usuario y contar las búsquedas
          df_agrupado = filtrados.groupby('username').size().reset_index(name='búsquedas')
          # Ordenar el dataframe de mayor a menor según la columna 'búsquedas'
          df_agrupado = df_agrupado.sort_values(by='búsquedas', ascending=False)
          fig = px.bar(
              df_agrupado, 
              x='username', 
              y='búsquedas',
              title=f'Búsquedas por usuario (semana {inicio_str} - {fin_str})',
              labels={'username': 'Usuario', 'búsquedas': 'Número de búsquedas'}
          )

          
          # Crear rangos personalizados para los yticks basados en los datos reales
          max_busquedas = df_agrupado['búsquedas'].max()

          # Crear marcas personalizadas que sean fáciles de leer
          # Para este caso específico con valores que llegan a ~600
          ticks = [50*i for i in range(20)]
          # Filtrar solo los ticks que son relevantes para nuestros datos
          ticks = [t for t in ticks if t <= max_busquedas + 50]

          # Actualizar la configuración del gráfico
          fig.update_layout(
              yaxis=dict(
                  tickmode='array',
                  tickvals=ticks,
                  range=[0, max_busquedas * 1.1],  # Dar un poco de espacio arriba
                  title=dict(
                      text="<b>Total de búsquedas</b>",
                      font=dict(size=20)
                  ),
                  gridcolor='lightgray',  # Líneas de cuadrícula más sutiles
                  # Garantizar que las líneas de cuadrícula aparezcan en cada marca
                  showgrid=True
              ),
              xaxis=dict(
                  title=dict(
                      text="<b>Usuario</b>",
                      font=dict(size=20)
                  )
              ),
              # Mejorar el diseño general
              plot_bgcolor='white',  # Fondo blanco para mejor legibilidad
              margin=dict(t=50, r=20, b=100, l=50),  # Márgenes para evitar cortes
          )

          # Agregar etiquetas de valor encima de cada barra para facilitar la lectura
          fig.update_traces(
              texttemplate='%{y}',  # Mostrar el valor exacto
              textposition='outside',  # Colocar el texto fuera de la barra
              textfont=dict(size=14)  # Tamaño de fuente adecuado
          )

          # Opcional: Agregar una línea de promedio para dar contexto
          promedio = df_agrupado['búsquedas'].mean()
          fig.add_hline(
              y=promedio, 
              line_dash="dash", 
              line_color="red",
              annotation_text=f"Promedio: {promedio:.1f}",
              annotation_position="top right",
              annotation_font=dict(
              color="red",  # Aquí se define el color rojo para el texto
              size=14
          )
          )
          
      elif 'usuario' in tipo_reporte.lower() and 'todos' not in tipo_reporte.lower():
          # Seleccionar el usuario "busqueda_usuario"
          filtrados = filtrados[filtrados['username'] == busqueda_usuario]
          # Agrupar por día y contar las búsquedas
          filtrados['día'] = filtrados['fecha'].dt.strftime('%d/%m')
          df_agrupado = filtrados.groupby('día').size().reset_index(name='búsquedas')
          fig = px.bar(
              df_agrupado,
              x='día',
              y='búsquedas',
              title=f'Total de búsquedas diarias (semana {inicio_str} - {fin_str})',
              labels={'día': 'Día del mes', 'búsquedas': 'Número de búsquedas'}
              )
      
          # Crear rangos personalizados para los yticks basados en los datos reales
          max_busquedas = df_agrupado['búsquedas'].max()

          # Crear marcas personalizadas que sean fáciles de leer
          # Para este caso específico con valores que llegan a ~600
          ticks = [10*i for i in range(20)]
          # Filtrar solo los ticks que son relevantes para nuestros datos
          ticks = [t for t in ticks if t <= max_busquedas + 50]

          # Actualizar la configuración del gráfico
          fig.update_layout(
              yaxis=dict(
                  tickmode='array',
                  tickvals=ticks,
                  range=[0, max_busquedas * 1.1],  # Dar un poco de espacio arriba
                  title=dict(
                      text="<b>Número de búsquedas</b>",
                      font=dict(size=20)
                  ),
                  gridcolor='lightgray',  # Líneas de cuadrícula más sutiles
                  # Garantizar que las líneas de cuadrícula aparezcan en cada marca
                  showgrid=True
              ),
              xaxis=dict(dtick=1, tickmode='linear',
                  title=dict(
                      text="<b>Día del mes</b>",
                      font=dict(size=20)  
                  )
              ),
              # Mejorar el diseño general
              plot_bgcolor='white',  # Fondo blanco para mejor legibilidad
              margin=dict(t=50, r=20, b=100, l=50),  # Márgenes para evitar cortes
          )

          # Agregar etiquetas de valor encima de cada barra para facilitar la lectura
          fig.update_traces(
              texttemplate='%{y}',  # Mostrar el valor exacto
              textposition='outside',  # Colocar el texto fuera de la barra
              textfont=dict(size=14)  # Tamaño de fuente adecuado
          )

          # Opcional: Agregar una línea de promedio para dar contexto
          promedio = df_agrupado['búsquedas'].mean()
          fig.add_hline(
              y=promedio, 
              line_dash="dash", 
              line_color="red",
              annotation_text=f"Promedio: {promedio:.1f}",
              annotation_position="top right",
              annotation_font=dict(
              color="red",  # Aquí se define el color rojo para el texto
              size=14
          )
          )
      
      return fig

  def generar_grafico_diario(datos, fecha, tipo_reporte):
      # Convertir a datetime si es necesario
      if isinstance(fecha, str):
          fecha = datetime.strptime(fecha, '%Y-%m-%d')
      
      fecha_inicio = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0)
      fecha_fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
      
      # Filtrar datos por la fecha seleccionada
      datos['fecha'] = pd.to_datetime(datos['timestamp'])
      filtrados = datos[
          (datos['fecha'] >= fecha_inicio) & 
          (datos['fecha'] <= fecha_fin)
      ]
      
      if filtrados.empty:
          st.warning(f"No hay datos para el {fecha.strftime('%d/%m/%Y')}")
          return None
      
      if 'búsquedas' in tipo_reporte.lower():
          if 'usuario' in tipo_reporte.lower() and 'todos' in tipo_reporte.lower():
            # Agrupar por usuario y contar las búsquedas
            df_agrupado = filtrados.groupby('username').size().reset_index(name='búsquedas')
            # Ordenar el dataframe de mayor a menor según la columna 'búsquedas'
            df_agrupado = df_agrupado.sort_values(by='búsquedas', ascending=False)
            fig = px.bar(
                df_agrupado, 
                x='username', 
                y='búsquedas',
                title=f'Total de búsquedas por usuario ({fecha.strftime("%d/%m/%Y")})'
            )

            # Crear rangos personalizados para los yticks basados en los datos reales
            max_busquedas = df_agrupado['búsquedas'].max()

            # Crear marcas personalizadas que sean fáciles de leer
            # Para este caso específico con valores que llegan a ~600
            ticks = [50*i for i in range(20)]
            # Filtrar solo los ticks que son relevantes para nuestros datos
            ticks = [t for t in ticks if t <= max_busquedas + 50]

            # Actualizar la configuración del gráfico
            fig.update_layout(
                yaxis=dict(
                    tickmode='array',
                    tickvals=ticks,
                    range=[0, max_busquedas * 1.1],  # Dar un poco de espacio arriba
                    title=dict(
                        text="<b>Total de búsquedas</b>",
                        font=dict(size=20)
                    ),
                    gridcolor='lightgray',  # Líneas de cuadrícula más sutiles
                    # Garantizar que las líneas de cuadrícula aparezcan en cada marca
                    showgrid=True
                ),
                xaxis=dict(
                    title=dict(
                        text="<b>Usuario</b>",
                        font=dict(size=20)
                    )
                ),
                # Mejorar el diseño general
                plot_bgcolor='white',  # Fondo blanco para mejor legibilidad
                margin=dict(t=50, r=20, b=100, l=50),  # Márgenes para evitar cortes
            )

            # Agregar etiquetas de valor encima de cada barra para facilitar la lectura
            fig.update_traces(
                texttemplate='%{y}',  # Mostrar el valor exacto
                textposition='outside',  # Colocar el texto fuera de la barra
                textfont=dict(size=14)  # Tamaño de fuente adecuado
            )

            # Opcional: Agregar una línea de promedio para dar contexto
            promedio = df_agrupado['búsquedas'].mean()
            fig.add_hline(
                y=promedio, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Promedio: {promedio:.1f}",
                annotation_position="top right",
                annotation_font=dict(
                color="red",  # Aquí se define el color rojo para el texto
                size=14
            )
            )
          elif 'usuario' in tipo_reporte.lower() and 'todos' not in tipo_reporte.lower():
              # Seleccionar el usuario "busqueda_usuario"
              filtrados = filtrados[filtrados['username'] == busqueda_usuario]
              # Agrupar por usuario y contar las búsquedas
              df_agrupado = filtrados.groupby('username').size().reset_index(name='búsquedas')
              # Hacer desglose por hora del dia
              filtrados['hora'] = filtrados['timestamp'].dt.hour
              df_agrupado = filtrados.groupby(['username', 'hora']).size().reset_index(name='búsquedas')
              fig = px.bar(
                  df_agrupado, 
                  x='hora', 
                  y='búsquedas',
                  title=f'Total de búsquedas por usuario ({fecha.strftime("%d/%m/%Y")})'
              )

              # Crear rangos personalizados para los yticks basados en los datos reales
              max_busquedas = df_agrupado['búsquedas'].max()

              # Crear marcas personalizadas que sean fáciles de leer
              # Para este caso específico con valores que llegan a ~600
              ticks = [5*i for i in range(20)]
              # Filtrar solo los ticks que son relevantes para nuestros datos
              ticks = [t for t in ticks if t <= max_busquedas + 50]

              # Actualizar la configuración del gráfico
              fig.update_layout(
                  yaxis=dict(
                      tickmode='array',
                      tickvals=ticks,
                      range=[0, max_busquedas * 1.1],  # Dar un poco de espacio arriba
                      title=dict(
                          text="<b>Número de búsquedas</b>",
                          font=dict(size=20)
                      ),
                      gridcolor='lightgray',  # Líneas de cuadrícula más sutiles
                      # Garantizar que las líneas de cuadrícula aparezcan en cada marca
                      showgrid=True
                  ),
                  xaxis=dict(dtick=1, tickmode='linear',
                      title=dict(
                          text="<b>Día del mes</b>",
                          font=dict(size=20)  
                      )
                  ),
                  # Mejorar el diseño general
                  plot_bgcolor='white',  # Fondo blanco para mejor legibilidad
                  margin=dict(t=50, r=20, b=100, l=50),  # Márgenes para evitar cortes
              )

              # Agregar etiquetas de valor encima de cada barra para facilitar la lectura
              fig.update_traces(
                  texttemplate='%{y}',  # Mostrar el valor exacto
                  textposition='outside',  # Colocar el texto fuera de la barra
                  textfont=dict(size=14)  # Tamaño de fuente adecuado
              )

              # Opcional: Agregar una línea de promedio para dar contexto
              promedio = df_agrupado['búsquedas'].mean()
              fig.add_hline(
                  y=promedio, 
                  line_dash="dash", 
                  line_color="red",
                  annotation_text=f"Promedio: {promedio:.1f}",
                  annotation_position="top right",
                  annotation_font=dict(
                  color="red",  # Aquí se define el color rojo para el texto
                  size=14
              )
              )                 
      return fig

  def generar_grafico_personalizado(datos, fecha_inicio, fecha_fin, tipo_reporte):
      # Convertir a datetime si es necesario
      if isinstance(fecha_inicio, str):
          fecha_inicio = pd.Timestamp(fecha_inicio)
      if isinstance(fecha_fin, str):
          fecha_fin = pd.Timestamp(fecha_fin)
      
      # Asegurar que la fecha de fin incluya todo el día
      fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
      
      # Calcular el número de días en el rango
      dias = (fecha_fin - fecha_inicio).days + 1
      
      # Filtrar datos por el rango de fechas seleccionado
      datos['fecha'] = pd.to_datetime(datos['timestamp'])
      filtrados = datos[
          (datos['fecha'] >= fecha_inicio) & 
          (datos['fecha'] <= fecha_fin)
      ]
      
      # Determinar el mejor agrupamiento según el rango de días
      if dias <= 31:  # Si es un mes o menos, agrupar por día
          filtrados['grupo'] = filtrados['fecha'].dt.strftime('%d/%m')
          label_x = 'Día'
          group_by = 'grupo'
      else:  # Si es más de 6 meses, agrupar por mes
          filtrados['grupo'] = filtrados['fecha'].dt.strftime('%b %Y')
          label_x = 'Mes'
          group_by = 'grupo'
          
      if filtrados.empty:
          st.warning(f"No hay datos para el periodo del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}")
          return None
      
      if 'usuario' in tipo_reporte.lower() and 'todos' in tipo_reporte.lower():
          # Agrupar por usuario  y contar las búsquedas
          df_agrupado = filtrados.groupby(['username']).size().reset_index(name='búsquedas')
          # Ordenar el dataframe de mayor a menor según la columna 'búsquedas'
          df_agrupado = df_agrupado.sort_values(by='búsquedas', ascending=False)
          fig = px.bar(
              df_agrupado, 
              x='username', 
              y='búsquedas',
              title=f'Búsquedas por usuario ({fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")})',
              labels={'username': 'Usuario', 'búsquedas': 'Número de búsquedas'}
          )

          # Crear rangos personalizados para los yticks basados en los datos reales
          max_busquedas = df_agrupado['búsquedas'].max()

          # Crear marcas personalizadas que sean fáciles de leer
          # Para este caso específico con valores que llegan a ~600
          ticks = [50*i for i in range(20)]
          # Filtrar solo los ticks que son relevantes para nuestros datos
          ticks = [t for t in ticks if t <= max_busquedas + 50]

          # Actualizar la configuración del gráfico
          fig.update_layout(
              yaxis=dict(
                  tickmode='array',
                  tickvals=ticks,
                  range=[0, max_busquedas * 1.1],  # Dar un poco de espacio arriba
                  title=dict(
                      text="<b>Total de búsquedas</b>",
                      font=dict(size=20)
                  ),
                  gridcolor='lightgray',  # Líneas de cuadrícula más sutiles
                  # Garantizar que las líneas de cuadrícula aparezcan en cada marca
                  showgrid=True
              ),
              # Mejorar el diseño general
              plot_bgcolor='white',  # Fondo blanco para mejor legibilidad
              margin=dict(t=50, r=20, b=100, l=50),  # Márgenes para evitar cortes
          )

          # Agregar etiquetas de valor encima de cada barra para facilitar la lectura
          fig.update_traces(
              texttemplate='%{y}',  # Mostrar el valor exacto
              textposition='outside',  # Colocar el texto fuera de la barra
              textfont=dict(size=14)  # Tamaño de fuente adecuado
          )

          # Opcional: Agregar una línea de promedio para dar contexto
          promedio = df_agrupado['búsquedas'].mean()
          fig.add_hline(
              y=promedio, 
              line_dash="dash", 
              line_color="red",
              annotation_text=f"Promedio: {promedio:.1f}",
              annotation_position="top right",
              annotation_font=dict(
              color="red",  # Aquí se define el color rojo para el texto
              size=14
          )
          )
      elif 'usuario' in tipo_reporte.lower() and 'todos' not in tipo_reporte.lower():
          # Seleccionar el usuario "busqueda_usuario" y agrupar por dias o meses segun corresponda
          filtrados = filtrados[filtrados['username'] == busqueda_usuario]
          df_agrupado = filtrados.groupby([group_by]).size().reset_index(name='búsquedas')
          fig = px.bar(
              df_agrupado, 
              x='grupo', 
              y='búsquedas',
              title=f'Búsquedas totales ({fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")})',
              labels={'grupo': label_x, 'búsquedas': 'Número de búsquedas'}
          )

          # Crear rangos personalizados para los yticks basados en los datos reales
          max_busquedas = df_agrupado['búsquedas'].max()

          # Crear marcas personalizadas que sean fáciles de leer
          # Para este caso específico con valores que llegan a ~600
          ticks = [5*i for i in range(20)]
          # Filtrar solo los ticks que son relevantes para nuestros datos
          ticks = [t for t in ticks if t <= max_busquedas + 50]

          # Actualizar la configuración del gráfico
          fig.update_layout(
              yaxis=dict(
                  tickmode='array',
                  tickvals=ticks,
                  range=[0, max_busquedas * 1.1],  # Dar un poco de espacio arriba
                  title=dict(
                      text="<b>Número de búsquedas</b>",
                      font=dict(size=20)
                  ),
                  gridcolor='lightgray',  # Líneas de cuadrícula más sutiles
                  # Garantizar que las líneas de cuadrícula aparezcan en cada marca
                  showgrid=True
              ),             
              # Mejorar el diseño general
              plot_bgcolor='white',  # Fondo blanco para mejor legibilidad
              margin=dict(t=50, r=20, b=100, l=50),  # Márgenes para evitar cortes
          )

          # Agregar etiquetas de valor encima de cada barra para facilitar la lectura
          fig.update_traces(
              texttemplate='%{y}',  # Mostrar el valor exacto
              textposition='outside',  # Colocar el texto fuera de la barra
              textfont=dict(size=14)  # Tamaño de fuente adecuado
          )

          # Opcional: Agregar una línea de promedio para dar contexto
          promedio = df_agrupado['búsquedas'].mean()
          fig.add_hline(
              y=promedio, 
              line_dash="dash", 
              line_color="red",
              annotation_text=f"Promedio: {promedio:.1f}",
              annotation_position="top right",
              annotation_font=dict(
              color="red",  # Aquí se define el color rojo para el texto
              size=14
          )
          )  
      
      return fig

  # Función principal que se ejecutaría cuando el usuario interactúa con la interfaz
  def mostrar_grafico(datos_uso, eleccion_reporte, periodo, **kwargs):
      if periodo == 'Mensual':
          mes = kwargs.get('busqueda_mensual_mes')
          ano = kwargs.get('busqueda_mensual_ano')
          return generar_grafico_mensual(datos_uso, mes, ano, eleccion_reporte)
      
      elif periodo == 'Semanal':
          semana = kwargs.get('busqueda_semanal')
          return generar_grafico_semanal(datos_uso, semana, eleccion_reporte)
      
      elif periodo == 'Diario':
          fecha = kwargs.get('busqueda_diaria')
          return generar_grafico_diario(datos_uso, fecha, eleccion_reporte)
      
      elif periodo == 'Personalizado':
          fecha_inicio = kwargs.get('fecha_inicio')
          fecha_fin = kwargs.get('fecha_fin')
          return generar_grafico_personalizado(datos_uso, fecha_inicio, fecha_fin, eleccion_reporte)
      
      return None

  # Obtener los datos
  datos_uso = get_search_logs()
  datos_uso = datos_uso[~datos_uso['username'].isin(st.secrets["admins"])]
  col_left, col_right = st.columns([1, 1])
  with col_left:
      subcols_left = st.columns([1, 1, 1])
      with subcols_left[0]:
         generar_reporte = st.button("Generar Reporte")
      with subcols_left[1]:
         if st.button("Volver al buscador"):
            st.switch_page("main.py")
  if generar_reporte:
      with st.spinner("Generando gráfico..."):
          if periodo == 'Mensual':
              fig = mostrar_grafico(datos_uso, eleccion_reporte, periodo, 
                                  busqueda_mensual_mes=busqueda_mensual_mes,
                                  busqueda_mensual_ano=busqueda_mensual_ano)
          
          elif periodo == 'Semanal':
              fig = mostrar_grafico(datos_uso, eleccion_reporte, periodo,
                                  busqueda_semanal=busqueda_semanal)
          
          elif periodo == 'Diario':
              fig = mostrar_grafico(datos_uso, eleccion_reporte, periodo,
                                  busqueda_diaria=busqueda_diaria)
          
          elif periodo == 'Personalizado':
              fig = mostrar_grafico(datos_uso, eleccion_reporte, periodo,
                                  fecha_inicio=fecha_inicio,
                                  fecha_fin=fecha_fin)
      if fig:
        st.plotly_chart(fig, use_container_width=False)
              