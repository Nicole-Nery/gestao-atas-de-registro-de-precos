@import url('https://fonts.cdnfonts.com/css/rawline');

html, body, .stApp * {
    font-family: 'Rawline', sans-serif !important;
    color: #333333;
}

/* Cor principal personalizada */
:root {
    --primary-color: #1E90FF; /* azul Dodger Blue */
    --primary-color-light: #63B3ED; /* azul claro para hover */
}

/* Aplicar nos elementos principais */
.stButton>button {
    background-color: var(--primary-color) !important;
    color: white !important;
    border: none !important;
}

.stButton>button:hover {
    background-color: var(--primary-color-light) !important;
    color: white !important;
}

/* Slider */
.css-1cpxqw2 .stSlider .st-cg {
    background-color: var(--primary-color) !important;
}

.css-1cpxqw2 .stSlider .st-cg:hover {
    background-color: var(--primary-color-light) !important;
}

/* Checkbox marcada */
input:checked + div:after {
    background-color: var(--primary-color) !important;
}
