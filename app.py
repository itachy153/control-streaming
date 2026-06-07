import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# Configuración de la aplicación móvil y PC
st.set_page_config(page_title="Streaming Control", page_icon="📺", layout="centered")

st.title("📺 Control de Streaming")
st.markdown("Gestión de ventas y cobros por WhatsApp.")

# Enlace de exportación de Google corregido
URL_DIRECTA = "https://google.com"

try:
    # Leer como archivo web directo usando motor python para evitar conflictos regionales
    df = pd.read_csv(URL_DIRECTA, sep=None, engine='python', encoding='utf-8')
    df.columns = [str(c).upper().strip() for c in df.columns]
    error_conexion = False
except Exception as e:
    error_conexion = True
    df = pd.DataFrame(columns=["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"])

# Asegurar que existan todas las columnas
columnas_necesarias = ["CLIENTE", "PLATAFORMA", "CUENTA", "VENCIMIENTO", "PRECIO", "MONEDA", "TELEFONO", "ESTADO"]
for col in columnas_necesarias:
    if col not in df.columns:
        df[col] = ""

# Sistema de Pestañas
tab1, tab2 = st.tabs(["📊 Clientes y Cobros", "➕ Nueva Venta"])

with tab1:
    if error_conexion:
        st.error("Error al conectar con la base de datos de Google Sheets. Asegúrate de que la hoja esté compartida de forma pública.")
    else:
        df["CLIENTE_LIMPIO"] = df["CLIENTE"].astype(str).str.strip()
        df_validos = df[(df["CLIENTE_LIMPIO"] != "") & (df["CLIENTE_LIMPIO"].str.lower() != "nan") & (df["CLIENTE_LIMPIO"].str.lower() != "none")].copy()
        
        if df_validos.empty:
            st.info("No hay registros activos en tu hoja de Google Sheets. Asegúrate de tener al menos una fila rellena debajo de los títulos.")
        else:
            # --- LÓGICA DE PROCESAMIENTO DE DATOS ---
            df_validos["ESTADO_LIMPIO"] = df_validos["ESTADO"].astype(str).str.strip().str.lower()
            
            # Crear columnas auxiliares para cálculos matemáticos seguros
            precios_numericos = []
            dias_calculados = []
            alertas_vencido = []
            textos_dias = []
            prioridad_orden = [] # Menor número = más arriba en la lista

            for index, row in df_validos.iterrows():
                # 1. Limpieza de precio para el panel de ganancias
                try:
                    p = float(str(row["PRECIO"]).replace(",", ".").strip())
                except:
                    p = 0.0
                precios_numericos.append(p)
                
                # 2. Cálculo de fechas y días restantes
                fecha_venc_str = str(row['VENCIMIENTO']).strip()
                dias_restantes = 999
                dias_texto = "📅 Fecha lista"
                vencido = False
                prioridad = 3 # Por defecto cuenta al día o pagada
                
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
                            prioridad = 1 # Vence hoy va arriba
                        else:
                            dias_texto = f"🚨 Vencido hace {abs(dias_restantes)} días"
                            vencido = True
                            prioridad = 0 # Vencidos van de primeritos arriba
                    except:
                        dias_texto = "📅 Fecha sin formato válido"
                
                # Forzar prioridad si explícitamente dice pendiente/vencido en estado
                estado_str = str(row['ESTADO_LIMPIO'])
                if "pendiente" in estado_str or "vencido" in estado_str:
                    if prioridad > 1:
                        prioridad = 2 # Pendientes no vencidos van al medio
                
                dias_calculados.append(dias_restantes)
                alertas_vencido.append(vencido)
                textos_dias.append(dias_texto)
                prioridad_orden.append(prioridad)

            # Inyectar las columnas procesadas al dataframe
            df_validos["PRECIO_NUM"] = precios_numericos
            df_validos["DIAS_NUM"] = dias_calculados
            df_validos["ALERTA_VENCIDO"] = alertas_vencido
            df_validos["TEXTO_DIAS"] = textos_dias
            df_validos["PRIORIDAD"] = prioridad_orden

            # --- MEJORA 1: PANEL DE GANANCIAS ---
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
            
            # Aplicar filtros visuales
            if filtro == "Pendiente":
                df_filtrado = df_validos[df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]
            elif filtro == "Pagado":
                df_filtrado = df_validos[~df_validos["ESTADO_LIMPIO"].str.contains("pendiente|vencido", na=False)]
            else:
                df_filtrado = df_validos.copy()
                
            if busqueda:
                df_filtrado = df_filtrado[df_filtrado["CLIENTE_LIMPIO"].str.lower().str.contains(busqueda, na=False)]
            
            # MEJORA 2: Ordenar automáticamente (Vencidos -> Pendientes -> Pagados)
            df_filtrado = df_filtrado.sort_values(by="PRIORIDAD", ascending=True)

            if df_filtrado.empty:
                st.warning("No se encontraron clientes con los filtros seleccionados.")
                
            # Desplegar tarjetas de clientes
            for index, row in df_filtrado.iterrows():
                cliente_nombre = str(row['CLIENTE_LIMPIO'])
                
                with st.container(border=True):
                    col_info, col_accion = st.columns(2)
                    
                    with col_info:
                        st.markdown(f"**👤 {cliente_nombre}**")
                        st.caption(f"🎬 {str(row['PLATAFORMA'])} | 🔑 {str(row['CUENTA'])}")
                        st.text(f"📅 Fecha de corte: {str(row['VENCIMIENTO'])}")
                        
                        # Mostrar indicador de días restantes
                        if row["ALERTA_VENCIDO"] or "pendiente" in str(row['ESTADO_LIMPIO']) or "vencido" in str(row['ESTADO_LIMPIO']):
                            st.markdown(f"<span style='color:#ff4b4b; font-weight:bold;'>{row['TEXTO_DIAS']}</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span style='color:#09ab3b; font-weight:bold;'>{row['TEXTO_DIAS']}</span>", unsafe_allow_html=True)
                        
                        moneda_str = str(row['MONEDA']).replace('nan', '').replace('NaN', '').strip()
                        st.markdown(f"💰 **{str(row['PRECIO'])} {moneda_str}**")
                    
                    with col_accion:
                        if "pendiente" in str(row['ESTADO_LIMPIO']) or "vencido" in str(row['ESTADO_LIMPIO']) or str(row['ESTADO_LIMPIO']) == "":
                            st.error("🔴 Estado: Pendiente")
                        else:
                            st.success("🟢 Estado: Pagado")
                        
                        # Mensaje automático inteligente
                        if row["ALERTA_VENCIDO"]:
                            mensaje = f"Hola {cliente_nombre}, te saludo para recordarte que tu pantalla de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) se encuentra vencida. El monto a transferir para reactivar el servicio es de {str(row['PRECIO'])} {moneda_str}. ¡Muchas gracias!"
                        else:
                            mensaje = f"Hola {cliente_nombre}, te saludo para recordarte que tu pantalla de {str(row['PLATAFORMA'])} ({str(row['CUENTA'])}) vence el {str(row['VENCIMIENTO'])}. El monto a transferir es de {str(row['PRECIO'])} {moneda_str}. ¡Muchas gracias!"
                            
                        mensaje_web = urllib.parse.quote(mensaje)
                        
                        tel_sucio = str(row['TELEFONO']).strip()
                        tel_limpio = "".join(filter(str.isdigit, tel_sucio.split('.')))
                        
                        url_ws = f"https://wa.me{tel_limpio}?text={mensaje_web}"
                        
                        st.markdown(
                            f'<a href="{url_ws}" target="_blank">'
                            f'<button style="width:100%; background-color:#25D366; color:white; '



