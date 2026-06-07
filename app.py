import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# Enlace de exportación directa universal de tu documento (sin caché)
URL_FINAL = "https://google.com"

try:
    # Leer el archivo ignorando la memoria caché para forzar la actualización inmediata
    df = pd.read_csv(URL_FINAL, sep=None, engine='python', encoding='utf-8')
    # Convertir todas las columnas a mayúsculas limpias sin espacios
    df.columns = [str(c).upper().strip() for c in df.columns]
except Exception as e:
    st.error("Error al conectar con la base de datos de Google Sheets.")
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"])

# Asegurar que existan todas las columnas del negocio
columnas_necesarias = ["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"]
for col in columnas_necesarias:
    if col not in df.columns:
        df[col] = ""

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    st.subheader("Lista de Clientes")
    
    # Limpiar espacios en blanco de la columna principal
    df["CLIENTE_LIMPIO"] = df["CLIENTE"].astype(str).str.strip()
    df_validos = df[(df["CLIENTE_LIMPIO"] != "") & (df["CLIENTE_LIMPIO"].str.lower() != "nan") & (df["CLIENTE_LIMPIO"].str.lower() != "none")]
    
    if df_validos.empty:
        st.info("No hay registros activos en tu hoja de Google Sheets. Asegúrate de tener al menos una fila rellena debajo de los títulos.")
    else:
        # MEJORA 1: Buscador por nombre de cliente
        busqueda = st.text_input("🔍 Buscar cliente por nombre:", "").strip().lower()
        
        # Filtro por estado
        filtro = st.selectbox("Filtrar por Estado:", ["Todos", "Pendiente", "Pagado"])
        
        df_validos["ESTADO_LIMPIO"] = df_validos["ESTADO"].astype(str).str.strip().str.lower()
        
        # Aplicar filtro de estado
        if filtro == "Pendiente":
            df_filtrado = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]
        elif filtro == "Pagado":
            df_filtrado = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pagado|activo", na=False)]
        else:
            df_filtrado = df_validos
            
        # Aplicar filtro de búsqueda por texto
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado["CLIENTE_LIMPIO"].str.lower().str.contains(busqueda, na=False)]
            
        if df_filtrado.empty:
            st.warning("No se encontraron clientes con los filtros seleccionados.")
            
        for index, row in df_filtrado.iterrows():
            cliente_nombre = str(row['CLIENTE_LIMPIO'])
            if cliente_nombre == "" or cliente_nombre.lower() == "nan":
                continue
                
            # MEJORA 2: Calcular los días restantes de forma dinámica
            fecha_venc_str = str(row['VENCIMIENTO']).strip()
            dias_texto = ""
            alerta_vencido = False
            
            try:
                # Intentar procesar formatos comunes de fecha (DD/MM/YYYY o YYYY-MM-DD)
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
                    alerta_vencido = True
                else:
                    dias_texto = f"🚨 Vencido hace {abs(dias_restantes)} días"
                    alerta_vencido = True
            except:
                dias_texto = "📅 Fecha sin formato válido"

            with st.container(border=True):
                col_info, col_accion = st.columns(2)
                
                with col_info:
                    st.markdown(f"**👤 {cliente_nombre}**")
                    st.caption(f"🎬 {str(row['PLATAFORMA'])} | 🔑 {str(row['CUENTA'])}")
                    st.text(f"📅 Fecha de corte: {fecha_venc_str}")
                    
                    # Mostrar el contador de días con un diseño llamativo si está vencido
                    if alerta_vencido:
                        st.markdown(f"<span style='color:#ff4b4b; font-weight:bold;'>{dias_texto}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:#09ab3b; font-weight:bold;'>{dias_texto}</span>", unsafe_allow_html=True)
                    
                    moneda_str = str(row['MONEDA']).replace('nan', '').replace('NaN', '').strip()
                    precio_str = str(row['PRECIO']).strip()
                    st.markdown(f"💰 **{precio_str} {moneda_str}**")
                
                with col_accion:
                    estado_str = str(row['ESTADO_LIMPIO'])
                    if "pendiente" in estado_str or "vencido" in estado_str or estado_str == "" or estado_str == "nan":
                        st.error("🔴 Estado: Pendiente")
                    else:
                        st.success("🟢 Estado: Pagado")
                    
                    # Mensaje automático inteligente que incluye los días si ya se venció
                    if alerta_vencido:
                        mensaje = f"Hola {cliente_nombre}, te saludo para recordarte que tu pantalla de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) se encuentra vencida. El monto a transferir para reactivar el servicio es de {precio_str} {moneda_str}. ¡Muchas gracias!"
                    else:
                        mensaje = f"Hola {cliente_nombre}, te saludo para recordarte que tu pantalla de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) vence el {str(row['VENCIMIENTO'])}. El monto a transferir es de {precio_str} {moneda_str}. ¡Muchas gracias!"
                        
                    mensaje_web = urllib.parse.quote(mensaje)
                    
                    # Limpieza total del teléfono
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
    st.warning("⚠️ Nota: Puedes añadir tus clientes directamente desde tu aplicación de Google Sheets en tu celular o PC, y aparecerán en este panel móvil al instante en tiempo real.")

