"""
Módulo de autenticación para el Dashboard Epidemiológico IGSS Escuintla
Sistema de login simple con contraseña única
"""

import streamlit as st
from config import COLORS

# Contraseña de acceso
PASSWORD = "Epidemiologia-IGSS-2025"


def check_password():
    """
    Verifica si el usuario ha ingresado la contraseña correcta.

    Returns:
        bool: True si está autenticado, False en caso contrario
    """

    # Verificar si ya está autenticado en session_state
    if st.session_state.get("authenticated", False):
        return True

    # Mostrar pantalla de login
    render_login_screen()

    return False


def render_login_screen():
    """
    Renderiza la pantalla de login con diseño profesional
    """

    # Centrar el contenido
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Espacio superior
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Logo y título
        st.markdown(
            f"""
            <div style='text-align: center; padding: 2rem;'>
                <h1 style='color: {COLORS['primary']}; font-size: 2.5rem; margin-bottom: 0.5rem;'>
                    📊 Dashboard Epidemiológico
                </h1>
                <h2 style='color: {COLORS['secondary']}; font-size: 1.5rem; font-weight: 500;'>
                    IGSS Escuintla
                </h2>
                <p style='color: #666; font-size: 1rem; margin-top: 1rem;'>
                    Sistema de Análisis de Morbilidad 2018-2025
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Espacio
        st.markdown("<br>", unsafe_allow_html=True)

        # Cuadro de login
        st.markdown(
            f"""
            <div style='background-color: {COLORS['background_alt']};
                        padding: 2rem;
                        border-radius: 10px;
                        border-left: 5px solid {COLORS['primary']};
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: {COLORS['text']}; text-align: center; margin-bottom: 1.5rem;'>
                    🔐 Acceso Restringido
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Campo de contraseña
        password_input = st.text_input(
            "Ingrese la contraseña de acceso:",
            type="password",
            key="password_input",
            placeholder="Contraseña"
        )

        # Botón de login
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            login_button = st.button("🔓 Ingresar", use_container_width=True)

        # Verificar contraseña
        if login_button:
            if password_input == PASSWORD:
                st.session_state["authenticated"] = True
                st.success("✅ Acceso concedido. Redirigiendo...")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta. Intente nuevamente.")

        # Footer de login
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align: center; color: #888; font-size: 0.9rem;'>
                <p>Instituto Guatemalteco de Seguridad Social</p>
                <p>Departamento de Epidemiología - Región Escuintla</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def logout():
    """
    Cierra la sesión del usuario
    """
    st.session_state["authenticated"] = False
    st.rerun()


def render_logout_button():
    """
    Renderiza un botón de cerrar sesión en el sidebar
    """
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        logout()
