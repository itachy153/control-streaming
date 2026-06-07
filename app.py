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
    # Leer la hoja de cálculo
    df = pd.read_csv(URL_CSV)
    # Forzar que todas las columnas leídas pasen a mayúsculas limpias
    df.columns = [str(c).upper().strip() for c in df.columns]
except Exception as e:
    st.error("Error al leer los datos de Google Sheets.")
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "TELEFONO", "ESTADO"])

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    st.subheader("Lista de Clientes")
    
    # CORRECCIÓN: Se simplifica la validación para evitar el AttributeError
    if df.empty:
        st.info("No hay registros activos en tu hoja de Google Sheets.")
    else:
        filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
        
        # Convertir columna ESTADO a texto limpio
        df["ESTADO"] = df["ESTADO"].astype(str).str.strip()
        df_filtrado = df if filtro == "Todos" else df[df["ESTADO"].str.lower() == filtro.lower()]
        
        for index, row in df_filtrado.iterrows():
            if pd.isna(row['CLIENTE']) or str(row['CLIENTE']).strip() == "":
                continue
                
            with st.container(border=True):
                col_info, col_accion = st.columns(2)
                
                with col_info:
                    st.markdown(f"**👤 {row['CLIENTE']}**")
                    st.caption(f"🎬 {row['PLATAFORMA']} | 🔑 {row['CUENTA']}")
                    st.text(f"📅 Vence: {row['VENCIMIENTO']}")
                    try:
                        precio_val = float(row['PRECIO'])
                        st.markdown(f"💰 **${precio_val:.2f}**")
                    except:
                        st.markdown(f"💰 **${row['PRECIO']}**")
                
                with col_accion:
                    estado_str = str(row['ESTADO']).lower()
                    if "pendiente" in estado_str or "vencido" in estado_str:
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
    st.warning("⚠️ Nota: Para registrar nuevos clientes desde este formulario móvil de forma directa, se requiere configurar la API avanzada de Google. Temporalmente, puedes añadir tus clientes directamente en tu aplicación de Google Sheets de tu celular y aparecerán aquí al instante.")
