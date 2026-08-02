import streamlit as st

from src.application.use_cases.login_user import AuthenticationError
from src.bootstrap import build_authentication_service


def render_login_page() -> bool:
    if "authenticated_user" in st.session_state:
        return True

    st.title("Ingreso a Plataforma Perfil de Cliente")
    st.caption("Ingrese sus credenciales para continuar.")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

    if not submitted:
        return False

    authentication_service = build_authentication_service()

    try:
        authenticated_user = authentication_service.login(
            username=username,
            password=password,
        )
    except AuthenticationError:
        st.error("Credenciales inválidas.")
        return False

    st.session_state["authenticated_user"] = authenticated_user
    st.rerun()

    return True


def render_logout_button() -> None:
    authenticated_user = st.session_state.get("authenticated_user")

    if authenticated_user is None:
        return

    with st.sidebar:
        st.caption(f"Usuario: {authenticated_user.full_name}")
        st.caption(f"Rol: {authenticated_user.role}")

        if st.button("Cerrar sesión"):
            del st.session_state["authenticated_user"]
            st.rerun()
