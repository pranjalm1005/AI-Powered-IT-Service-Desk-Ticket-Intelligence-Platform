import streamlit as st
from user_app import user_router, render_user_header
from admin_app import admin_router, render_admin_header

# -------------------------
# SESSION DEFAULTS
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.email = None

if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = None

if "theme" not in st.session_state:
    st.session_state.theme = "light"

# ----------------------------------------
# Streamlit Page Config
# ----------------------------------------
st.set_page_config(
    page_title="Nsight ITSM AI Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------
# THEME CONFIGURATION
# ----------------------------------------
def get_theme_colors():
    if st.session_state.theme == "dark":
        return {
            "bg_primary": "#1a1a2e",
            "bg_secondary": "#16213e",
            "bg_card": "#0f3460",
            "text_primary": "#eaeaea",
            "text_secondary": "#94a3b8",
            "accent": "#e94560",
            "accent_hover": "#c93a52",
            "border": "#2d3748",
            "shadow": "rgba(0, 0, 0, 0.4)",
            "status_open_bg": "#fff3cd",
            "status_open_text": "#856404",
            "status_progress_bg": "#cce5ff",
            "status_progress_text": "#004085",
            "status_resolved_bg": "#d4edda",
            "status_resolved_text": "#155724",
        }
    else:
        return {
            "bg_primary": "#f8f9fa",
            "bg_secondary": "#ffffff",
            "bg_card": "#ffffff",
            "text_primary": "#2c3e50",
            "text_secondary": "#64748b",
            "accent": "#667eea",
            "accent_hover": "#5568d3",
            "border": "#e2e8f0",
            "shadow": "rgba(0, 0, 0, 0.08)",
            "status_open_bg": "#fff3cd",
            "status_open_text": "#856404",
            "status_progress_bg": "#cce5ff",
            "status_progress_text": "#004085",
            "status_resolved_bg": "#d4edda",
            "status_resolved_text": "#155724",
        }

# ----------------------------------------
# DYNAMIC STYLING
# ----------------------------------------
def apply_theme_styling():
    colors = get_theme_colors()
    texture_url = "data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"
    
    st.markdown(f"""
        <style>
            /* Global Layout */
            .stApp {{
                background: {colors['bg_primary']};
                background-image: url("{texture_url}");
                background-attachment: fixed;
                color: {colors['text_primary']};
            }}
            
            /* Sidebar Styling */
            [data-testid="stSidebar"] {{
                background: {colors['bg_secondary']};
                background-image: url("{texture_url}");
                border-right: 1px solid {colors['border']};
            }}
            
            [data-testid="stSidebar"] .stMarkdown {{
                color: {colors['text_primary']};
            }}

            /* Header Styling */
            .main-header {{
                background: {colors['bg_secondary']};
                padding: 1.5rem 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px {colors['shadow']};
                margin-bottom: 2rem;
                border: 1px solid {colors['border']};
            }}

            /* Login Container */
            .login-container {{
                background: {colors['bg_secondary']};
                padding: 3rem 2.5rem;
                border-radius: 16px;
                box-shadow: 0 8px 32px {colors['shadow']};
                border: 1px solid {colors['border']};
                max-width: 450px;
                margin: 0 auto;
            }}
            
            .login-title {{
                text-align: center;
                color: {colors['text_primary']};
                font-size: 1.75rem;
                font-weight: 600;
                margin-bottom: 2rem;
                letter-spacing: -0.5px;
            }}

            /* Ticket Cards */
            .ticket-card {{
                background: {colors['bg_card']};
                padding: 1.4rem;
                border-radius: 12px;
                box-shadow: 0 2px 8px {colors['shadow']};
                margin-bottom: 1rem;
                border-left: 4px solid {colors['accent']};
                transition: all 0.3s ease;
                border: 1px solid {colors['border']};
            }}
            
            .ticket-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 16px {colors['shadow']};
                border-left-color: {colors['accent_hover']};
            }}

            .ticket-id {{
                font-size: 0.875rem;
                color: {colors['accent']};
                font-weight: 600;
                margin-bottom: 0.5rem;
                letter-spacing: 0.3px;
            }}
            
            .ticket-title {{
                font-size: 1.05rem;
                font-weight: 600;
                color: {colors['text_primary']};
                margin-bottom: 0.5rem;
            }}
            
            .ticket-meta {{
                font-size: 0.85rem;
                color: {colors['text_secondary']};
                margin-top: 0.5rem;
            }}

            /* Info Box */
            .info-box {{
                background: {colors['bg_card']};
                padding: 1.2rem;
                border-radius: 10px;
                border-left: 4px solid {colors['accent']};
                margin-top: 1rem;
                border: 1px solid {colors['border']};
                color: {colors['text_primary']};
            }}

            /* Metric Cards */
            .metric-card {{
                background: {colors['bg_card']};
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 8px {colors['shadow']};
                border-left: 4px solid {colors['accent']};
                text-align: center;
                transition: all 0.3s ease;
                border: 1px solid {colors['border']};
            }}
            
            .metric-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px {colors['shadow']};
            }}
            
            .metric-card h3 {{
                color: {colors['text_secondary']};
                font-size: 0.9rem;
                font-weight: 500;
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .metric-card h1 {{
                color: {colors['text_primary']};
                font-size: 2.2rem;
                font-weight: 700;
                margin: 0;
            }}

            /* Status Badges */
            .status-badge {{
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.3px;
                display: inline-block;
            }}
            
            .status-open {{
                background: {colors['status_open_bg']};
                color: {colors['status_open_text']};
                border: 1px solid #ffc107;
            }}
            
            .status-in-progress {{
                background: {colors['status_progress_bg']};
                color: {colors['status_progress_text']};
                border: 1px solid #2196F3;
            }}
            
            .status-resolved {{
                background: {colors['status_resolved_bg']};
                color: {colors['status_resolved_text']};
                border: 1px solid #28a745;
            }}

            /* Detail Container */
            .detail-container {{
                background: {colors['bg_card']};
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 2px 12px {colors['shadow']};
                border: 1px solid {colors['border']};
            }}

            /* Ticket Header */
            .ticket-header {{
                background: linear-gradient(135deg, {colors['accent']} 0%, {colors['accent_hover']} 100%);
                color: white;
                padding: 1.5rem 2rem;
                border-radius: 12px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 12px {colors['shadow']};
            }}

            /* Input Fields */
            .stTextInput input, .stTextArea textarea {{
                background: {colors['bg_card']} !important;
                color: {colors['text_primary']} !important;
                border: 1px solid {colors['border']} !important;
                border-radius: 8px !important;
                font-size: 0.95rem !important;
            }}
            
            .stTextInput input::placeholder, .stTextArea textarea::placeholder {{
                color: {colors['text_secondary']} !important;
            }}

            /* Buttons */
            .stButton button {{
                background: {colors['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.6rem 1.5rem;
                font-weight: 600;
                font-size: 0.9rem;
                transition: all 0.3s ease;
                letter-spacing: 0.3px;
            }}
            
            .stButton button:hover {{
                background: {colors['accent_hover']};
                transform: translateY(-1px);
                box-shadow: 0 4px 12px {colors['shadow']};
            }}

            /* Theme Toggle */
            .theme-toggle {{
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 999;
                background: {colors['bg_card']};
                padding: 0.5rem;
                border-radius: 50px;
                box-shadow: 0 2px 8px {colors['shadow']};
                border: 1px solid {colors['border']};
            }}

            /* Logout Button */
            .logout-btn {{
                background: #e94560 !important;
                color: white !important;
            }}
            
            .logout-btn:hover {{
                background: #c93a52 !important;
            }}

            /* Expander Styling */
            .streamlit-expanderHeader {{
                background: {colors['bg_card']} !important;
                color: {colors['text_primary']} !important;
                border: 1px solid {colors['border']} !important;
                border-radius: 8px !important;
                font-size: 0.95rem !important;
            }}

            /* Radio Buttons */
            .stRadio > label {{
                color: {colors['text_primary']} !important;
                font-weight: 500 !important;
            }}

            /* Dataframe */
            .stDataFrame {{
                background: {colors['bg_card']} !important;
                border: 1px solid {colors['border']} !important;
                border-radius: 8px !important;
            }}

            /* Selectbox */
            .stSelectbox > div > div {{
                background: {colors['bg_card']} !important;
                color: {colors['text_primary']} !important;
                border: 1px solid {colors['border']} !important;
            }}
            
            /* Navigation Menu */
            .nav-menu {{
                background: {colors['bg_card']};
                padding: 1rem;
                border-radius: 12px;
                margin-bottom: 2rem;
                box-shadow: 0 2px 8px {colors['shadow']};
                border: 1px solid {colors['border']};
            }}
            
            .nav-item {{
                padding: 0.8rem 1.2rem;
                margin: 0.3rem 0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                color: {colors['text_primary']};
                font-weight: 500;
                font-size: 0.95rem;
            }}
            
            .nav-item:hover {{
                background: {colors['accent']};
                color: white;
                transform: translateX(5px);
            }}
            
            .nav-item.active {{
                background: {colors['accent']};
                color: white;
                box-shadow: 0 2px 8px {colors['shadow']};
            }}

        </style>
    """, unsafe_allow_html=True)

# ----------------------------------------
# LOGOUT FUNCTION
# ----------------------------------------
def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.email = None
    st.session_state.selected_ticket_id = None
    st.rerun()

# ----------------------------------------
# THEME TOGGLE
# ----------------------------------------
def render_theme_toggle():
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col2:
        theme_icon = "🌙" if st.session_state.theme == "light" else "☀️"
        if st.button(theme_icon, key="theme_toggle", help="Toggle Theme"):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()
    
    with col3:
        if st.button("🚪 Logout", key="logout_btn", help="Logout"):
            logout()

# ----------------------------------------
# LOGIN PAGE
# ----------------------------------------
def login_page():
    apply_theme_styling()
    
    # Theme toggle on login page
    col_theme = st.columns([8, 1])[1]
    with col_theme:
        theme_icon = "🌙" if st.session_state.theme == "light" else "☀️"
        if st.button(theme_icon, key="login_theme_toggle", help="Toggle Theme"):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class='login-container'>
                <div class='login-title'>
                    🔐 Nsight ITSM Portal
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        email = st.text_input(
            "Email Address",
            placeholder="your.email@nsight.com",
            key="login_email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔓 Sign In", use_container_width=True, key="login_submit"):
            # ADMIN LOGIN
            if email.lower() == "admin@nsight.com" and password == "Admin@123":
                st.session_state.logged_in = True
                st.session_state.role = "admin"
                st.session_state.email = email
                st.success("✅ Admin login successful!")
                st.rerun()

            # USER LOGIN
            elif password == "User@123" and email.endswith("@nsight.com"):
                st.session_state.logged_in = True
                st.session_state.role = "user"
                st.session_state.email = email
                st.success("✅ Login successful!")
                st.rerun()

            else:
                st.error("❌ Invalid credentials. Please try again.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center; color: #64748b; font-size: 0.85rem;'>"
            "Admin: admin@nsight.com / Admin@123<br>"
            "User: any@nsight.com / User@123"
            "</div>",
            unsafe_allow_html=True
        )

# ----------------------------------------
# MAIN APP
# ----------------------------------------
def main():
    apply_theme_styling()
    
    if not st.session_state.logged_in:
        login_page()
        return

    # Render theme toggle and logout
    render_theme_toggle()

    if st.session_state.role == "admin":
        render_admin_header()
        admin_router()
    else:
        render_user_header()
        user_router()

if __name__ == "__main__":
    main()