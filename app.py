import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# URL de tu hoja de cálculo integrada
URL_HOJA = "https://google.com"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=URL_HOJA, ttl="0")
    # Forzar que todas las columnas leídas pasen a mayúsculas limpias
    df.columns = [str(c).upper().strip() for c in df.columns]
except Exception as e:
    st.error("Error al conectar con Google Sheets. Verifica los permisos.")
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "TELEFONO", "ESTADO"])

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    st.subheader("Lista de Clientes")
    
    if df.empty or df.iloc.isnull().all().all():
        st.info("No hay registros activos en tu hoja de Google Sheets.")
    else:
        filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
        
        df["ESTADO"] = df["ESTADO"].astype(str).str.strip()
        df_filtrado = df if filtro == "Todos" else df[df["ESTADO"].str.lower() == filtro.lower()]
        
        for index, row in df_filtrado.iterrows():
            if pd.isna(row['CLIENTE']) or str(row['CLIENTE']).strip() == "":
                continue
                
            with st.container(border=True):
                # CORRECCIÓN: Se agrega el número 2 para indicar dos columnas
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
                    if str(row['ESTADO']).lower() == "pendiente" or str(row['ESTADO']).lower() == "vencido":
                        st.error("🔴 Pendiente")
                    else:
                        st.success("🟢 Pagado")
                    
                    mensaje = f"Hola {row['CLIENTE']}, te escribo para recordarte que tu cuenta de {row['PLATAFORMA']} ({row['CUENTA']}) vence el {row['VENCIMIENTO']}. El total a pagar es de ${row['PRECIO']}. ¡Muchas gracias!"
                    mensaje_web = urllib.parse.quote(mensaje)
                    
                    # Limpieza del teléfono para generar el enlace de WhatsApp
                    tel_final = str(row['TELEFONO']).strip()
                    if '.' in tel_final:
                        tel_final = tel_final.split('.')[0]
                    
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
    
    with st.form("formulario_venta", clear_on_submit=True):
        cliente_input = st.text_input("Nombre del Cliente *")
        plataforma_input = st.selectbox("Plataforma", ["Netflix", "Disney+", "Max", "Prime Video", "Spotify", "Magis TV", "Otro"])
        cuenta_input = st.text_input("Perfil / Cuenta asignada")
        vencimiento_input = st.date_input("Fecha de Vencimiento")
        precio_input = st.number_input("Precio de venta ($)", min_value=0.0, step=0.5)
        telefono_input = st.text_input("Teléfono del cliente *")
        estado_input = st.selectbox("Estado del pago", ["Pendiente", "Pagado"])
        
        guardar_boton = st.form_submit_button("💾 Registrar en Google Sheets")
        
        if guardar_boton:
            if cliente_input and telefono_input:
                tel_limpio = "".join(filter(str.isdigit, telefono_input))
                
                nueva_fila = pd.DataFrame([{
                    "CLIENTE": cliente_input,
                    "PLATAFORMA": plataforma_input,
                    "CUENTA": cuenta_input,
                    "VENCIMIENTO": str(vencimiento_input),
                    "PRECIO": precio_input,
                    "TELEFONO": tel_limpio,
                    "ESTADO": estado_input
                }])
                
                df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
                conn.update(spreadsheet=URL_HOJA, data=df_actualizado)
                
                st.success(f"¡Venta de {cliente_input} guardada con éxito!")
                st.rerun()
            else:
                st.error("Por favor completa los campos obligatorios (*).")
