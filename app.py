import streamlit as st
import pandas as pd
import urllib.parse

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# Formato de exportación directa en formato de hoja abierta
URL_FORMATO = "https://google.com"

try:
    # Leer la hoja con codificación universal de caracteres
    df = pd.read_csv(URL_FORMATO, encoding='utf-8')
    # Convertir todas las columnas encontradas a mayúsculas limpias sin espacios
    df.columns = [str(c).upper().replace('"', '').replace("'", "").strip() for c in df.columns]
except Exception as e:
    st.error("Error al leer los datos de Google Sheets.")
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"])

# Garantizar que existan todas las columnas necesarias (Incluyendo MONEDA)
columnas_necesarias = ["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"]
for col in columnas_necesarias:
    if col not in df.columns:
        df[col] = ""

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    st.subheader("Lista de Clientes")
    
    # Filtrar registros válidos quitando filas vacías
    df_validos = df[df["CLIENTE"].notna() & (df["CLIENTE"].astype(str).str.strip() != "")]
    
    if df_validos.empty:
        st.info("No hay registros activos en tu hoja de Google Sheets. Asegúrate de tener al menos una fila rellena debajo de los títulos.")
    else:
        filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
        
        # Normalizar la columna de estado
        df_validos["ESTADO"] = df_validos["ESTADO"].astype(str).str.strip().str.lower()
        
        if filtro == "Pendiente":
            df_filtrado = df_validos[df_validos["ESTADO"].str.contains("pendiente|vencido", na=False)]
        elif filtro == "Pagado":
            df_filtrado = df_validos[df_validos["ESTADO"].str.contains("pagado|activo", na=False)]
        else:
            df_filtrado = df_validos
            
        for index, row in df_filtrado.iterrows():
            cliente_nombre = str(row['CLIENTE']).replace('"', '').strip()
            if cliente_nombre.lower() == "nan" or cliente_nombre == "":
                continue
                
            with st.container(border=True):
                col_info, col_accion = st.columns(2)
                
                with col_info:
                    st.markdown(f"**👤 {cliente_nombre}**")
                    st.caption(f"🎬 {str(row['PLATAFORMA'])} | 🔑 {str(row['CUENTA'])}")
                    st.text(f"📅 Vence: {str(row['VENCIMIENTO'])}")
                    
                    # Mostrar el precio junto a la moneda asignada (Ej: 4.5 USD)
                    moneda_str = str(row['MONEDA']).replace('nan', '').strip()
                    st.markdown(f"💰 **{str(row['PRECIO'])} {moneda_str}**")
                
                with col_accion:
                    estado_str = str(row['ESTADO'])
                    if "pendiente" in estado_str or "vencido" in estado_str:
                        st.error("🔴 Pendiente/Vencido")
                    else:
                        st.success("🟢 Pagado")
                    
                    # Mensaje incluyendo el monto y el tipo de moneda
                    mensaje = f"Hola {cliente_nombre}, te escribo para recordarte que tu cuenta de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) vence el {str(row['VENCIMIENTO'])}. El total a pagar es de {str(row['PRECIO'])} {moneda_str}. ¡Muchas gracias!"
                    mensaje_web = urllib.parse.quote(mensaje)
                    
                    # Limpieza total del teléfono quitando letras, espacios y puntos decimales
                    tel_limpio = "".join(filter(str.isdigit, str(row['TELEFONO'])))
                    
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
    st.warning("⚠️ Nota: Puedes añadir tus clientes directamente desde la aplicación de Google Sheets en tu celular o PC, y aparecerán en este panel móvil al instante en tiempo real.")



