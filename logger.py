import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime
import json
import streamlit as st
import logging
import pytz

# Configurar logging
logger = logging.getLogger(__name__)

def get_gspread_client():
    """
    Obtiene un cliente de gspread autenticado utilizando las credenciales guardadas en Streamlit Secrets.
    """
    try:
        # Obtener credenciales desde secrets.toml
        service_account_info = st.secrets["gcp_service_account"]
        
        # Cargar las credenciales directamente desde el objeto JSON
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )
        
        # Crear cliente
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        logger.error(f"Error al obtener cliente gspread: {str(e)}")
        raise e

def log_search(username, search_params, considerar_ofertas, proveedores):
    """
    Registra una búsqueda en una hoja de Google Sheets
    
    Args:
        username (str): Nombre del usuario que realizó la búsqueda
        search_params (dict): Términos de búsqueda y operadores lógicos
        considerar_ofertas (str): Si se consideraron ofertas o no
        search_time (float): Tiempo que tomó la búsqueda
    """
    try:
        # Obtener el ID de la hoja de Google Sheets desde Streamlit Secrets
        spreadsheet_id = st.secrets["url"]["gsheet_id"]
        
        # Obtener cliente de gspread
        client = get_gspread_client()
        
        # Abrir la hoja de cálculo
        sheet = client.open_by_key(spreadsheet_id)
        
        # Obtener la hoja donde guardaremos los logs
        # Si no existe, la creamos
        sheet_name = "search_logs"
        try:
            worksheet = sheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            # Agregar encabezados
            headers = [
                "timestamp", "username", "contains_0", "search_term_0", "logical_1", "contains_1", "search_term_1", "logical_2", "contains_2", "search_term_2", "logical_3", "contains_3", "search_term_3", "considerar_ofertas", "search_query",
                "proveedores"
            ]
            worksheet.update('A1:P1', [headers])
        
        # Extraer los términos de búsqueda en un formato más legible
        search_terms = []
        words = []
        contains_or_not = []
        logicals = []
        for i in range(4):  # Suponiendo que hay 4 cajas de búsqueda
            term = search_params.get(f'search_{i}', '')
            logical = search_params.get(f'logical_{i}', '')
            contains = search_params.get(f'contains_{i}', '')
            words.append(term)
            contains_or_not.append(contains)
            logicals.append(logical)
            if term:
                if i == 0:
                    search_terms.append(f"{contains} '{term}'")
                else:
                    search_terms.append(f"{logical} {contains} '{term}'")
        
        search_query = " ".join(search_terms)
        
        # Preparar datos para el log
        timestamp = datetime.datetime.now(pytz.timezone("America/Santiago")).strftime("%d-%m-%Y %H:%M:%S")
        log_data = [timestamp, username]
        for i in range(4):
            if i > 0:
              log_data.append(logicals[i])            
            log_data.append(contains_or_not[i])            
            log_data.append(words[i])
        log_data.append(considerar_ofertas)
        log_data.append(search_query)
        
        provs = ", ".join(proveedores)
        log_data.append(provs)
            
        # Agregar una nueva fila con los datos
        worksheet.append_row(log_data)
        
        logger.info(f"Búsqueda registrada para {username}: {search_query}")
        return True
    
    except Exception as e:
        logger.error(f"Error al registrar búsqueda en Google Sheets: {str(e)}")
        # No detener la aplicación si falla el logging
        return False

def get_search_logs():
    """
    Obtiene todos los registros de búsqueda de Google Sheets
    
    Returns:
        pandas.DataFrame: DataFrame con los registros de búsqueda
    """
    try:
        # Obtener el ID de la hoja de Google Sheets desde Streamlit Secrets
        spreadsheet_id = st.secrets["url"]["gsheet_id"]
        
        # Obtener cliente de gspread
        client = get_gspread_client()
        
        # Abrir la hoja de cálculo
        sheet = client.open_by_key(spreadsheet_id)
        
        # Obtener la hoja donde están los logs
        try:
            worksheet = sheet.worksheet("search_logs")
        except gspread.exceptions.WorksheetNotFound:
            # Si no existe la hoja, devolver DataFrame vacío
            return pd.DataFrame()
        
        # Obtener todos los datos
        data = worksheet.get_all_records()
        
        # Convertir a DataFrame
        df = pd.DataFrame(data)
        
        # Si el DataFrame no está vacío, convertir timestamp a datetime
        if not df.empty and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d-%m-%Y %H:%M:%S')
        
        return df
    
    except Exception as e:
        logger.error(f"Error al obtener logs de Google Sheets: {str(e)}")
        # Devolver DataFrame vacío en caso de error
        return pd.DataFrame()
