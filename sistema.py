st.markdown("""
    <style>
    :root {
        --primary-color: #1E90FF;
        --primary-color-light: #63B3ED;
    }

    .stButton>button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
    }

    .stButton>button:hover {
        background-color: var(--primary-color-light) !important;
        color: white !important;
    }

    .stSlider > div[data-baseweb="slider"] {
        color: var(--primary-color) !important;
    }

    input:checked + div:after {
        background-color: var(--primary-color) !important;
    }
    </style>
""", unsafe_allow_html=True)
