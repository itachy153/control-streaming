import streamlit as st
import pandas as pd
import urllib.parse

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# URL de exportación directa de tu Google Sheet en formato CSV
URL_CSV = "https://google.com"

try:
    # AJUSTE LATAM: Intentamos leer primero con punto y coma (;) que es el estándar de Google en la región
    try:
        df = pd.read_csv(URL_CSV, sep=';')
        # Si leyó mal y solo creó una columna, reintentamos con coma (,) tradicional
        if len(df.columns) <= 1:
            df = pd.read_csv(URL_CSV, sep=',')
    except:
        df = pd.read_csv(URL_CSV, sep=',')
        
    # LIMPIEZA TOTAL: Convertir columnas a mayúsculas, quitar espacios y caracteres raros
    df.columns = [str(c).upper().strip() for c in df.columns]
except Exception as e:
    st.error("Error al leer los datos de Google Sheets.")
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "TELEFONO", "ESTADO"])

# SEGURIDAD: Si alguna columna falta por temas de formato de Google, la creamos vacía para evitar caídas
columnas_necesarias = ["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "TELEFONO", "ESTADO"]
for col in columnas_necesarias:
    if col not in df.columns:
        df[col] = ""

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    st.subheader("Lista de Clientes")
    
    # Comprobar si hay datos reales
    if df.empty or df["CLIENTE"].dropna().str.strip().eq("").all():
        st.info("No hay registros activos en tu hoja de Google Sheets. Asegúrate de tener al menos una fila rellena debajo de los títulos.")
    else:
        filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
        
        # Convertir columna ESTADO a texto limpio de forma segura
        df["ESTADO"] = df["ESTADO"].astype(str).str.strip()
        df_filtrado = df if filtro == "Todos" else df[df["ESTADO"].str.lower() == filtro.lower()]
        
        for index, row in df_filtrado.iterrows():
            # Saltar filas vacías
            if pd.isna(row['CLIENTE']) or str(row['CLIENTE']).strip() == "" or str(row['CLIENTE']).strip().lower() == "nan":
                continue
                
            with st.container(border=True):
                col_info, col_accion = st.columns(2)
                
                with col_info:
                    st.markdown(f"**👤 {row['CLIENTE']}**")
                    st.caption(f"🎬 {row['PLATAFORMA']} | 🔑 {row['CUENTA']}")
                    st.text(f"📅 Vence: {row['VENCIMIENTO']}")
                    try:
                        precio_val = float(str(row['PRECIO']).replace(',', '.'))
                        st.markdown(f"💰 **${precio_val:.2f}**")
                    except:
                        st.markdown(f"💰 **${row['PRECIO']}**")
                
                with col_accion:
                    estado_str = str(row['ESTADO']).lower().strip()
                    if "pendiente" in estado_str or "vencido" in estado_str or estado_str == "nan" or estado_str == "":
                        st.error("🔴 Pendiente")
                    else:
                        st.success("🟢 Pagado")
                    
                    mensaje = f"Hola {row['CLIENTE']}, te escribo para recordarte que tu cuenta de {row['PLATAFORMA']} ({row['CUENTA']}) vence el {row['VENCIMIENTO']}. El total a pagar es de ${row['PRECIO']}. ¡Muchas gracias!"
                    mensaje_web = urllib.parse.quote(mensaje)
                    
                    # Limpieza estricta del número telefónico para evitar decimales (.0)
                    tel_sucio = str(row['TELEFONO']).strip()
                    if '.' in tel_sucio:
                        tel_final = tel_sucio.split('.')[0]
                    else:
                        tel_final = tel_sucio
                    
                    url_ws = f"https://wa.me{tel_final}?text={mensaje_web}"
                    
                    st.markdown(
                        f'<a href="{url_ws}" target="_blank">'
                        f'<button style="width:100%; background-color:#25D366; color:white; '
                        f'border:none; padding:10px; border-radius:8px; font-weight:bold; '
                        f'cursor:pointer;">💬 Cobrar</button></a>', 
                        unsafe_allow_html=True
                    )

with tab2:
    st.subheader("Registrar nueva pantalla")
    st.warning("⚠️ Nota: Puedes añadir tus clientes directamente desde la aplicación de Google Sheets en tu celular o PC, y aparecerán en este panel móvil de inmediato en tiempo real.")


