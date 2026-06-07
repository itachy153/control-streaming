import streamlit as st
import pandas as pd
import urllib.parse

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# Enlace de publicación directa (Ignora el error de pestañas y gid=0)
URL_PUBLICACION = "https://google.com"

try:
    # Leer directamente la tabla sin parámetros de consulta que bloqueen a Google
    df = pd.read_csv(URL_PUBLICACION, encoding='utf-8')
    # Limpiar exhaustivamente los nombres de las columnas
    df.columns = [str(c).upper().replace('"', '').replace("'", "").strip() for c in df.columns]
except Exception as e:
    st.error("Error al conectar con la base de datos de Google Sheets.")
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"])

# Asegurar la existencia de las columnas necesarias
columnas_necesarias = ["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"]
for col in columnas_necesarias:
    if col not in df.columns:
        df[col] = ""

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    st.subheader("Lista de Clientes")
    
    # Normalizar los nombres de los clientes quitando espacios y valores nulos
    df["CLIENTE_LIMPIO"] = df["CLIENTE"].astype(str).str.replace('"', '').str.strip()
    df_validos = df[(df["CLIENTE_LIMPIO"] != "") & (df["CLIENTE_LIMPIO"].str.lower() != "nan") & (df["CLIENTE_LIMPIO"].str.lower() != "none")]
    
    if df_validos.empty:
        st.info("No hay registros activos en tu hoja de Google Sheets. Asegúrate de tener al menos una fila rellena debajo de los títulos.")
    else:
        filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
        
        df_validos["ESTADO_LIMPIO"] = df_validos["ESTADO"].astype(str).str.replace('"', '').str.strip().str.lower()
        
        if filtro == "Pendiente":
            df_filtrado = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]
        elif filtro == "Pagado":
            df_filtrado = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pagado|activo", na=False)]
        else:
            df_filtrado = df_validos
            
        for index, row in df_filtrado.iterrows():
            cliente_nombre = str(row['CLIENTE_LIMPIO'])
            if cliente_nombre == "" or cliente_nombre.lower() == "nan":
                continue
                
            with st.container(border=True):
                col_info, col_accion = st.columns(2)
                
                with col_info:
                    st.markdown(f"**👤 {cliente_nombre}**")
                    st.caption(f"🎬 {str(row['PLATAFORMA']).replace('\"', '')} | 🔑 {str(row['CUENTA']).replace('\"', '')}")
                    st.text(f"📅 Vence: {str(row['VENCIMIENTO']).replace('\"', '')}")
                    
                    moneda_str = str(row['MONEDA']).replace('"', '').replace('nan', '').replace('NaN', '').strip()
                    precio_str = str(row['PRECIO']).replace('"', '').strip()
                    st.markdown(f"💰 **{precio_str} {moneda_str}**")
                
                with col_accion:
                    estado_str = str(row['ESTADO_LIMPIO'])
                    if "pendiente" in estado_str or "vencido" in estado_str:
                        st.error("🔴 Pendiente")
                    else:
                        st.success("🟢 Pagado")
                    
                    mensaje = f"Hola {cliente_nombre}, te escribo para recordarte que tu cuenta de {str(row['PLATAFORMA']).replace('\"', '')} ({str(row['CUENTA']).replace('\"', '')}) vence el {str(row['VENCIMIENTO']).replace('\"', '')}. El total a pagar es de {precio_str} {moneda_str}. ¡Muchas gracias!"
                    mensaje_web = urllib.parse.quote(mensaje)
                    
                    # Limpieza estricta de teléfono para el link de WhatsApp
                    tel_sucio = str(row['TELEFONO']).replace('"', '').strip()
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
