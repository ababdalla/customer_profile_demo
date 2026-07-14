from datetime import date

import streamlit as st

from profile_service import build_customer_profile


st.set_page_config(page_title="Perfil de Cliente", layout="wide")

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
   # kpis = profile["kpis"]

    st.subheader(cliente["nombre_completo"])

    #col1, col2, col3, col4 = st.columns(4)
    #col1.metric("Total creditos", f"Q {kpis['total_creditos']:,.2f}")
    #col2.metric("Total debitos", f"Q {kpis['total_debitos']:,.2f}")
    #col3.metric("Flujo neto", f"Q {kpis['flujo_neto']:,.2f}")
    #col4.metric("Cuentas", kpis["cantidad_cuentas"])

    tab1, tab2, tab3 = st.tabs(
        ["Resumen", "Productos",  "Relaciones"]
    )

    with tab1:
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

   #with tab3:
   #     st.write("### Consolidado mensual")
   #     st.dataframe(profile["consolidado"], use_container_width=True)
   #     st.write("### Causas de transaccion")
   #     st.dataframe(profile["causas"], use_container_width=True)

    with tab3:
        st.write("### Cuentas como firmante")
        st.dataframe(profile["cuentas_firmantes"], use_container_width=True)
        st.write("### Terceros relacionados")
        st.dataframe(profile["transacciones"], use_container_width=True)
        st.write("### ACH")
        st.dataframe(profile["ach"], use_container_width=True)
