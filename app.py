import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# URL de tu hoja de cálculo integrada
URL_HOJA = "https://docs.google.com/spreadsheets/d/1lfQtU9F0lTWmKtu8aVbfF-krBrH1_MyMls4dmaNHgIk/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ttl="0" obliga a la app a leer los datos reales en cada recarga
    df = conn.read(spreadsheet=URL_HOJA, ttl="0")
except Exception as e:
    st.error("Error al conectar con Google Sheets. Verifica que la hoja tenga permisos de Editor para cualquier persona con el enlace.")
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "TELEFONO", "ESTADO"])

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    st.subheader("Lista de Clientes")
    
    if df.empty or df.iloc[0].isnull().all():
        st.info("No hay registros activos en tu hoja de Google Sheets.")
    else:
        # Filtro rápido para el celular
        filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
        
        # Limpieza de espacios en blanco en la columna ESTADO para evitar fallos de filtrado
        df["ESTADO"] = df["ESTADO"].astype(str).str.strip()
        df_filtrado = df if filtro == "Todos" else df[df["ESTADO"].str.lower() == filtro.lower()]
        
        # Generar tarjetas adaptables a pantallas chicas y grandes
        for index, row in df_filtrado.iterrows():
            # Evita mostrar filas completamente vacías de la hoja
            if pd.isna(row['CLIENTE']):
                continue
                
            with st.container(border=True):
                col_info, col_accion = st.columns()
                
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
                    # Indicador visual de estado
                    if str(row['ESTADO']).lower() == "pendiente":
                        st.error("🔴 Pendiente")
                    else:
                        st.success("🟢 Pagado")
                    
                    # Formatear mensaje para WhatsApp
                    mensaje = f"Hola {row['CLIENTE']}, te escribo para recordarte que tu cuenta de {row['PLATAFORMA']} ({row['CUENTA']}) vence el {row['VENCIMIENTO']}. El total a pagar es de ${row['PRECIO']}. ¡Muchas gracias!"
                    mensaje_web = urllib.parse.quote(mensaje)
                    
                    # Link universal de WhatsApp (funciona en PC y Celular)
                    url_ws = f"https://wa.me{int(float(row['TELEFONO'])) if str(row['TELEFONO']).replace('.','',1).isdigit() else row['TELEFONO']}?text={mensaje_web}"
                    
                    # Botón llamativo para cobrar
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
        cuenta_input = st.text_input("Perfil / Cuenta asignada (Ej: Perfil 3 - Clave123)")
        vencimiento_input = st.date_input("Fecha de Vencimiento")
        precio_input = st.number_input("Precio de venta ($)", min_value=0.0, step=0.5)
        telefono_input = st.text_input("Teléfono del cliente *", help="Escribe el código de país sin el signo +. Ejemplo: 584123456789")
        estado_input = st.selectbox("Estado del pago", ["Pendiente", "Pagado"])
        
        guardar_boton = st.form_submit_button("💾 Registrar en Google Sheets")
        
        if guardar_boton:
            if cliente_input and telefono_input:
                # Limpiar el teléfono de espacios o caracteres extraños
                tel_limpio = "".join(filter(str.isdigit, telefono_input))
                
                # Crear la nueva fila de datos respetando las mayúsculas de tus columnas
                nueva_fila = pd.DataFrame([{
                    "CLIENTE": cliente_input,
                    "PLATAFORMA": plataforma_input,
                    "CUENTA": cuenta_input,
                    "VENCIMIENTO": str(vencimiento_input),
                    "PRECIO": precio_input,
                    "TELEFONO": tel_limpio,
                    "ESTADO": estado_input
                }])
                
                # Unir los datos viejos con los nuevos y subirlos
                df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
                conn.update(spreadsheet=URL_HOJA, data=df_actualizado)
                
                st.success(f"¡Venta de {cliente_input} guardada con éxito!")
                st.rerun()
            else:
                st.error("Por favor completa los campos obligatorios (*).")
