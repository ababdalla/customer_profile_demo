from datetime import date

import streamlit as st

from profile_service import build_customer_profile
from src.presentation.streamlit.login_page import render_login_page,render_logout_button


st.set_page_config(page_title="Perfil de Cliente", layout="wide")
is_authenticated = render_login_page()

if not is_authenticated:
    st.stop()

render_logout_button()

st.title("Perfil de Cliente")

with st.sidebar:
    st.header("Consulta")
    cliente_id = st.text_input("Cliente ID")
    fecha_inicio = st.date_input("Fecha inicio", value=date(2025, 4, 1))
    fecha_fin = st.date_input("Fecha fin", value=date(2026, 4, 1))
    generar = st.button("Generar perfil")

if generar:
    with st.spinner("Consultando datos del cliente..."):
        profile = build_customer_profile(cliente_id, fecha_inicio, fecha_fin)
    
    cliente = profile["cliente"]
    kpis = profile["kpis"]
    alertas = profile["alertas"]

    st.subheader(cliente["nombre_completo"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total creditos", f"Q {kpis['total_creditos']:,.2f}")
    col2.metric("Total debitos", f"Q {kpis['total_debitos']:,.2f}")
    col3.metric("Flujo neto", f"Q {kpis['flujo_neto']:,.2f}")
    col4.metric("Cuentas", kpis["cantidad_cuentas"])

    tab1, tab2, tab3,tab4 ,tab5= st.tabs(
            ["Resumen", "Productos", "Transacciones", "Relaciones", "info_alertas"]
    )

    with tab1:
        st.write(profile)
        st.write("### Perfil del cliente")
        st.write(
            {
                "Cliente ID": cliente["clienteid"],
                "DPI": cliente["dpi"],
                "NIT": cliente["nit"],
                "Tipo persona": cliente["tipo_persona"],
                "Estado": cliente["estado_cliente_sistema"],
                "RIC": cliente["ric"],
                "CPE": cliente["es_cpe"],
                "PEP": cliente["es_pep"],
                "Actividad economica": cliente["actividad_economica"],
                "Ingresos reportados": cliente["ingresos_reportados"],
            }
        )
        st.dataframe(cliente, use_container_width=True)

    with tab2:
        st.write("### Cuentas y productos")
        st.dataframe(profile["cuentas"], use_container_width=True)

    with tab3:
        st.write("### Consolidado mensual")
        st.dataframe(profile["consolidado"], use_container_width=True)
        st.write("### Causas de transaccion")
        st.dataframe(profile["causas"], use_container_width=True)

    with tab4:
        st.write("### Cuentas como firmante")
        st.dataframe(profile["cuentas_firmantes"], use_container_width=True)
        st.write("### Terceros relacionados")
        st.dataframe(profile["transacciones"], use_container_width=True)
        st.write("### ACH")
        st.dataframe(profile["ach"], use_container_width=True)

    with tab5:
        st.write("### DATOS DE LA DENUNCIA") 
        titular_df = alertas[alertas.get("parentesco").astype(str) == "TITULAR"] if "parentesco" in alertas.columns else alertas.iloc[0:0]
        base = titular_df.iloc[0] if not titular_df.empty else alertas.iloc[0]

        st.write(
            {
                "Número de caso:": base.get("numero_caso"),
                "Canal de recepción de denuncia:": base.get("canal_recepcion_denuncia"),
                "Clasificación:": base.get("clasificacion_denuncia"),
                "Fecha de recepción:":base.get("fecha_recepcion"),
                "Fecha de asignación:": base.get("fecha_asignacion"),
                "Contexto de la denuncia:": base.get("contexto_denuncia"), }
        )
        st.write("### DENUNCIADO") 
        st.write( 
            { 
                "Código de empleado:": base.get("cod_empleado_base"),
                "Fecha de Ingreso:": base.get("fecha_de_ingreso"),
                "Relación con GFA:": base.get("categoria_persona"),
                "Operador:": base.get("operador"),
                "Jornada:": base.get("jornada"),
                "Dependencia/Agencia:": base.get("unidad"),
                "Zona:": base.get("zona"),
                "División:": base.get("division"),
                # IMPORTANTÍSIMO: para que sea “tal cual”, replicamos la misma lógica del Excel (vicepresidencia = division)
                "Vicepresidencia:": base.get("division"),
                "Socio Estratégico:": base.get("socio_estrategico"),
                "Empresa:": base.get("empresa"),
                "Usuario Cobis:": base.get("usuario_cobis"),
                "Puesto:": base.get("puesto"),
                "Años de laborar en el banco:": base.get("anos_antiguedad"),
                # tal cual Excel: “Consecutivo Cobis” = cod_cliente
                "Consecutivo Cobis:": base.get("cod_cliente"),
                "Salario del colaborador:": base.get("ingreso_mensual"),
                "Usuario Bancolombia:": base.get("usuario_bancolombia"),
            }
        )
        st.write("### PERFILACIÓN")
        st.write("Perfilación de cliente")
        st.write(
            {

                "Nombre:": "N/A",
                "Consecutivo:": "N/A",
                "DPI:": "N/A",
                "Dirección:": "N/A",
                "Teléfono:": "N/A",
            }
        )
        st.write("Perfilación de colaborador")
        st.write(
            {
                
                "Nombre:": base.get("nombre_completo"),
                "Consecutivo:": base.get("cod_cliente"),
                "DPI:": base.get("cui"),
                "Dirección:": base.get("direccion"),
                "Teléfono:": base.get("telefono"),
                "Edad:": base.get("edad"),
            }
        )

        st.write("### PRODUCTOS")
        st.write("Módulo de Clientes del Escritorio BAM")
        
        df_prod = alertas[alertas["tipo_producto"].astype(str) != "TARJETA CREDITO"].copy() if "tipo_producto" in alertas.columns else alertas.iloc[0:0]

        if not df_prod.empty:
            df_view = (
                df_prod[
                    [
                        "agencia",
                        "tipo_producto",
                        "moneda",
                        "numero_producto",
                        "fecha_apertura",
                        "estado",
                    ]
                ]
                .rename(
                    columns={
                        "agencia": "Agencia de Apertura",
                        "tipo_producto": "Tipo producto",
                        "moneda": "Moneda",
                        "numero_producto": "Número producto",
                        "fecha_apertura": "Fecha apertura",
                        "estado": "Estado",
                    }
                )
            )
            st.dataframe(df_view, use_container_width=True)

        #Subtitulo: Tarjetas
        #Revisar porque solo me aparecen las tarjetas sin moneda asignada
        df_tc = alertas[alertas["tipo_producto"].astype(str)=="TARJETA CREDITO"].copy() if "tipo_producto" in alertas.columns else alertas.iloc[0:0]

        if not df_tc.empty:
            st.write('Consulta integrada de Tarjeta de Crédito objeto de investigación')
            df_vtc = (
                df_tc[
                    [
                        "numero_producto",
                        "descripcion_producto",
                        "moneda_tarjeta",
                        "estado",
                        "limite_credito_tc",
                        "saldo_actual_tc",
                    ]
                ]
                .rename(
                    columns={
                        "numero_producto": 'Número tarjeta',
                        "descripcion_producto": 'Tipo tarjeta',
                        "moneda_tarjeta":'Moneda',
                        "estado":'Estado',
                        "limite_credito_tc":'Límite',
                        "saldo_actual_tc": 'Saldo Actual',
                    }
                )
            )
            st.dataframe(df_vtc, use_container_width=True)

        # ===========FAMILIARES==============

        df_fam = alertas[alertas["parentesco"].astype(str) != "TITULAR"].copy() if "parentesco" in alertas.columns else alertas.iloc[0:0]
        if not df_fam.empty:
            st.write("### FAMILIARES COLABORADOR")
            df_fam["es_cliente"]=(df_fam["cod_cliente"].fillna("").astype(str).str.strip().replace("None","").ne("").map({True:"Sí", False: "No"}))
            df_fvw = (
                df_fam[
                    [
                        "nombre_completo",
                        "parentesco",
                        "profesion",
                        "es_cliente",
                        "cod_cliente",
                        "numero_producto",
                    ]
                ]
                .rename(
                    columns={
                        "nombre_completo": 'Nombre Familiar',
                        "parentesco": 'Parentesco',
                        "profesion":'Profesión o Actividad Económica',
                        "es_cliente":'Es cliente?',
                        "cod_cliente":'Código Cliente',
                        "numero_producto": 'Productos Activos',
                    }
                )
            )
            st.dataframe(df_fvw, use_container_width=True)

