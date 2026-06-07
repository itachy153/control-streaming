import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# EL ENLACE CORRECTO YA ESTÁ INTEGRADO AQUÍ ABAJO:
URL_FINAL = "https://google.com"

try:
    # Leer el archivo CSV web de forma directa sin pasar por st.connection
    df = pd.read_csv(URL_FINAL, encoding='utf-8')
    df.columns = [str(c).upper().strip() for c in df.columns]
    error_conexion = False
except Exception as e:
    error_conexion = True
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"])

# Asegurar que existan todas las columnas básicas para el negocio
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
        df["CLIENTE_LIMPIO"] = df["CLIENTE"].astype(str).str.strip()
        df_validos = df[(df["CLIENTE_LIMPIO"] != "") & (df["CLIENTE_LIMPIO"].str.lower() != "nan") & (df["CLIENTE_LIMPIO"].str.lower() != "none")].copy()
        
        if df_validos.empty:
            st.info("No hay registros activos en tu hoja de Google Sheets. Asegúrate de tener al menos una fila rellena debajo de los títulos.")
        else:
            df_validos["ESTADO_LIMPIO"] = df_validos["ESTADO"].astype(str).str.strip().str.lower()
            
            precios_numericos = []
            textos_dias = []
            alertas_vencido = []
            prioridades = []

            for index, row in df_validos.iterrows():
                try:
                    p = float(str(row["PRECIO"]).replace(',', '.').strip())
                except:
                    p = 0.0
                precios_numericos.append(p)
                
                fecha_venc_str = str(row['VENCIMIENTO']).strip()
                dias_texto = "📅 Fecha lista"
                vencido = False
                prioridad = 3
                
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
                            prioridad = 0
                    except:
                        dias_texto = f"📅 Vence: {fecha_venc_str}"
                
                estado_str = str(row['ESTADO_LIMPIO'])
                if "pendiente" in estado_str or "vencido" in estado_str:
                    if prioridad > 1:
                        prioridad = 2
                        
                alertas_vencido.append(vencido)
                textos_dias.append(dias_texto)
                prioridades.append(prioridad)
            
            df_validos["PRECIO_NUM"] = precios_numericos
            df_validos["TEXTO_DIAS"] = textos_dias
            df_validos["ALERTA_VENCIDO"] = alertas_vencido
            df_validos["PRIORIDAD"] = prioridades

            # --- PANEL DE GANANCIAS ---
            st.subheader("📊 Resumen del Mes")
            ganado = df_validos[~df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]["PRECIO_NUM"].sum()
            por_cobrar = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]["PRECIO_NUM"].sum()
            
            col_met1, col_met2 = st.columns(2)
            with col_met1:
                st.metric("💰 Dinero Cobrado", f"${ganado:.2f} USD")
            with col_met2:
                st.metric("🔴 Por Cobrar", f"${por_cobrar:.2f} USD")
            
            st.divider()

            # --- BUSCADOR Y FILTROS ---
            st.subheader("Lista de Clientes")
            busqueda = st.text_input("🔍 Buscar cliente por nombre:", "").strip().lower()
            filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
            
            if filtro == "Pendiente":
                df_filtrado = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]
            elif filtro == "Pagado":
                df_filtrado = df_validos[~df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]
            else:
                df_filtrado = df_validos.copy()
                
            if busqueda:
                df_filtrado = df_filtrado[df_filtrado["CLIENTE_LIMPIO"].str.lower().str.contains(busqueda, na=False)]
            
            df_filtrado = df_filtrado.sort_values(by="PRIORIDAD", ascending=True)

            if df_filtrado.empty:
                st.warning("No se encontraron clientes.")
            else:
                for index, row in df_filtrado.iterrows():
                    cliente_nombre = str(row['CLIENTE_LIMPIO'])
                    
                    with st.container(border=True):
                        col_info, col_accion = st.columns(2)
                        
                        with col_info:
                            st.markdown(f"**👤 {cliente_nombre}**")
                            st.caption(f"🎬 {str(row['PLATAFORMA'])} | 🔑 {str(row['CUENTA'])}")
                            st.text(f"📅 Vence: {str(row['VENCIMIENTO'])}")
                            
                            if row["ALERTA_VENCIDO"] or "pendiente" in str(row['ESTADO_LIMPIO']) or "vencido" in str(row['ESTADO_LIMPIO']):
                                st.markdown(f"<span style='color:#ff4b4b; font-weight:bold;'>{row['TEXTO_DIAS']}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color:#09ab3b; font-weight:bold;'>{row['TEXTO_DIAS']}</span>", unsafe_allow_html=True)
                            
                            moneda_str = str(row['MONEDA']).replace('nan', '').replace('NaN', '').strip()
                            precio_str = str(row['PRECIO']).strip()
                            st.markdown(f"💰 **{precio_str} {moneda_str}**")
                        
                        with col_accion:
                            if "pendiente" in str(row['ESTADO_LIMPIO']) or "vencido" in str(row['ESTADO_LIMPIO']):
                                st.error("🔴 Pendiente")
                            else:
                                st.success("🟢 Pagado")
                            
                            if row["ALERTA_VENCIDO"]:
                                mensaje = f"Hola {cliente_nombre}, te escribo para recordarte que tu cuenta de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) se encuentra vencida. El total a pagar para restablecer el servicio es de {precio_str} {moneda_str}. ¡Muchas gracias!"
                            else:
                                mensaje = f"Hola {cliente_nombre}, te escribo para recordarte que tu cuenta de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) vence el {str(row['VENCIMIENTO'])}. El total a pagar es de {precio_str} {moneda_str}. ¡Muchas gracias!"
                                
                            mensaje_web = urllib.parse.quote(mensaje)
                            
                            tel_sucio = str(row['TELEFONO']).strip()
                            tel_limpio = "".join(filter(str.isdigit, tel_sucio.split('.')))
                            
                            url_ws = f"https://wa.me{tel_limpio}?text={mensaje_web}"
                            
                            st.markdown(
                                f'<a href="{url_ws}" target="_blank">'
                                f'<button style="width:100%; background-color:#25D366; color:white; '
                                f'border:none; padding:10px; border-radius:8px; font-weight:bold; '
                                f'cursor:pointer;">💬 Cobrar</button></a>', 
                                unsafe_allow_html=True
                            )

with tab2:
    st.subheader("Registrar nueva pantalla")
    st.warning("⚠️ Nota: Añade tus clientes directamente desde tu archivo de Google Sheets en tu celular o PC y aparecerán en este panel móvil al instante en tiempo real.")



          



