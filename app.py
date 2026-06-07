import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# SOLUCIÓN DE ENLACE: Cambiado a /export?format=csv para que descargue la tabla real sin bloquearse
URL_PUBLICACION = https://docs.google.com/spreadsheets/d/1lfQtU9F0lTWmKtu8aVbfF-krBrH1_MyMls4dmaNHgIk/edit?usp=sharing


try:
    # Leer la tabla directamente desde los servidores de Google usando el motor Python
    df = pd.read_csv(URL_PUBLICACION, sep=None, engine='python', encoding='utf-8')
    # Limpiar exhaustivamente los nombres de las columnas pasándolas a mayúsculas
    df.columns = [str(c).upper().replace('"', '').replace("'", "").strip() for c in df.columns]
    error_conexion = False
except Exception as e:
    error_conexion = True
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"])

# Asegurar la existencia de las columnas necesarias
columnas_necesarias = ["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"]
for col in columnas_necesarias:
    if col not in df.columns:
        df[col] = ""

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    if error_conexion:
        st.error("Error al conectar con la base de datos de Google Sheets. Asegúrate de tener conexión a internet.")
    else:
        # Normalizar los nombres de los clientes quitando espacios y valores nulos
        df["CLIENTE_LIMPIO"] = df["CLIENTE"].astype(str).str.replace('"', '').str.strip()
        df_validos = df[(df["CLIENTE_LIMPIO"] != "") & (df["CLIENTE_LIMPIO"].str.lower() != "nan") & (df["CLIENTE_LIMPIO"].str.lower() != "none")].copy()
        
        if df_validos.empty:
            st.info("No hay registros activos en tu hoja de Google Sheets. Asegúrate de tener al menos una fila rellena debajo de los títulos.")
        else:
            # --- PROCESAMIENTO AVANZADO DE DATOS (Moneas, Fechas y Prioridades) ---
            df_validos["ESTADO_LIMPIO"] = df_validos["ESTADO"].astype(str).str.replace('"', '').str.strip().str.lower()
            
            precios_numericos = []
            textos_dias = []
            alertas_vencido = []
            prioridades = []

            for index, row in df_validos.iterrows():
                # 1. Limpiar precios para cálculos matemáticos del panel
                try:
                    p = float(str(row["PRECIO"]).replace('"', '').replace(',', '.').strip())
                except:
                    p = 0.0
                precios_numericos.append(p)
                
                # 2. Calcular días restantes dinámicamente según la fecha actual
                fecha_venc_str = str(row['VENCIMIENTO']).replace('"', '').strip()
                dias_texto = "📅 Fecha lista"
                vencido = False
                prioridad = 3  # Por defecto: pagado o al día
                
                if fecha_venc_str and fecha_venc_str.lower() != "nan" and fecha_venc_str != "":
                    try:
                        if "/" in fecha_venc_str:
                            fecha_venc = datetime.strptime(fecha_venc_str, "%d/%m/%Y").date()
                        else:
                            fecha_venc = datetime.strptime(fecha_venc_str, "%Y-%m-%d").date()
                        
                        hoy = datetime.now().date()
                        dias_restantes = (fecha_venc - hoy).days
                        
                        if dias_restantes > 0:
                            dias_texto = f"⏳ Quedan {dias_restantes} días de servicio"
                        elif dias_restantes == 0:
                            dias_texto = f"⚠️ ¡Vence HOY!"
                            vencido = True
                            prioridad = 1
                        else:
                            dias_texto = f"🚨 Vencido hace {abs(dias_restantes)} días"
                            vencido = True
                            prioridad = 0  # Los vencidos toman la prioridad más alta (arriba)
                    except:
                        dias_texto = f"📅 Vence: {fecha_venc_str}"
                
                # Forzar prioridad si explícitamente dice pendiente o vencido en la columna ESTADO
                estado_str = str(row['ESTADO_LIMPIO'])
                if "pendiente" in estado_str or "vencido" in estado_str:
                    if prioridad > 1:
                        prioridad = 2  # Los deudores no vencidos van al medio
                        
                alertas_vencido.append(vencido)
                textos_dias.append(dias_texto)
                prioridades.append(prioridad)
            
            # Inyectar cálculos al DataFrame de forma segura
            df_validos["PRECIO_NUM"] = precios_numericos
            df_validos["TEXTO_DIAS"] = textos_dias
            df_validos["ALERTA_VENCIDO"] = alertas_vencido
            df_validos["PRIORIDAD"] = prioridades

            # --- MEJORA 1: PANEL DE GANANCIAS ---
            st.subheader("📊 Resumen Económico del Mes")
            ganado = df_validos[~df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]["PRECIO_NUM"].sum()
            por_cobrar = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]["PRECIO_NUM"].sum()
            
            col_met1, col_met2 = st.columns(2)
            with col_met1:
                st.metric("💰 Dinero Cobrado", f"${ganado:.2f} USD")
            with col_met2:
                st.metric("🔴 Por Cobrar", f"${por_cobrar:.2f} USD")
            
            st.divider()

            # --- MEJORA 2 & 3: BUSCADOR Y FILTROS ---
            st.subheader("Lista de Clientes")
            busqueda = st.text_input("🔍 Buscar cliente por nombre:", "").strip().lower()
            filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
            
            # Filtrar por los menús desplegables
            if filtro == "Pendiente":
                df_filtrado = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]
            elif filtro == "Pagado":
                df_filtrado = df_validos[~df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]
            else:
                df_filtrado = df_validos.copy()
                
            if busqueda:
                df_filtrado = df_filtrado[df_filtrado["CLIENTE_LIMPIO"].str.lower().str.contains(busqueda, na=False)]
            
            # MEJORA 4: ORDEN AUTOMÁTICO (Vencidos -> Pendientes -> Pagados)
            df_filtrado = df_filtrado.sort_values(by="PRIORIDAD", ascending=True)

            if df_filtrado.empty:
                st.warning("No se encontraron clientes con los filtros seleccionados.")
            else:
                # Desplegar las tarjetas de información de cada cliente
                for index, row in df_filtrado.iterrows():
                    cliente_nombre = str(row['CLIENTE_LIMPIO'])
                    
                    with st.container(border=True):
                        col_info, col_accion = st.columns(2)
                        
                        with col_info:
                            st.markdown(f"**👤 {cliente_nombre}**")
                            st.caption(f"🎬 {str(row['PLATAFORMA']).replace('\"', '')} | 🔑 {str(row['CUENTA']).replace('\"', '')}")
                            st.text(f"📅 Vence: {str(row['VENCIMIENTO']).replace('\"', '')}")
                            
                            # Mostrar indicador de días en color dinámico (Rojo para alertas, verde para días al día)
                            if row["ALERTA_VENCIDO"] or "pendiente" in str(row['ESTADO_LIMPIO']) or "vencido" in str(row['ESTADO_LIMPIO']):
                                st.markdown(f"<span style='color:#ff4b4b; font-weight:bold;'>{row['TEXTO_DIAS']}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color:#09ab3b; font-weight:bold;'>{row['TEXTO_DIAS']}</span>", unsafe_allow_html=True)
                            
                            moneda_str = str(row['MONEDA']).replace('"', '').replace('nan', '').replace('NaN', '').strip()
                            precio_str = str(row['PRECIO']).replace('"', '').strip()
                            st.markdown(f"💰 **{precio_str} {moneda_str}**")
                        
                        with col_accion:
                            if "pendiente" in str(row['ESTADO_LIMPIO']) or "vencido" in str(row['ESTADO_LIMPIO']):
                                st.error("🔴 Pendiente")
                            else:
                                st.success("🟢 Pagado")
                            
                            # Mensaje automatizado inteligente según si el cliente ya está vencido o no
                            if row["ALERTA_VENCIDO"]:
                                mensaje = f"Hola {cliente_nombre}, te escribo para recordarte que tu cuenta de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) se encuentra vencida. El total a pagar para restablecer el servicio es de {precio_str} {moneda_str}. ¡Muchas gracias!"
                            else:
                                mensaje = f"Hola {cliente_nombre}, te escribo para recordarte que tu cuenta de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) vence el {str(row['VENCIMIENTO'])}. El total a pagar es de {precio_str} {moneda_str}. ¡Muchas gracias!"
                                
                            mensaje_web = urllib.parse.quote(mensaje)
                            
                            # Limpieza estricta de teléfono para el link universal de WhatsApp




