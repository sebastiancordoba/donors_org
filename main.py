import streamlit as st
import replicate
import os
import json
import pandas as pd

# Cargar el token de Replicate desde config.json
with open("config.json", "r") as f:
    config = json.load(f)

replicate_api = config.get("REPLICATE_API_TOKEN", "")

# Configurar la página
st.set_page_config(page_title="🦙💬 Generador de Correo para Donantes")

st.title('🦙💬 Generador de Correo para Donantes')

if not replicate_api:
    st.warning('No se encontró la clave API en config.json. Por favor agréguela antes de continuar.', icon='⚠️')
else:
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

# Modelo y parámetros fijos
llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
max_length = 128  # Correo corto

st.header("Subir la Lista de Donantes")
uploaded_file = st.file_uploader("Sube un archivo CSV con columnas 'Nombre' y 'Categoria'", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    # Asegurar que las columnas 'Nombre' y 'Categoria' existan
    if "Nombre" not in df.columns or "Categoria" not in df.columns:
        st.error("El CSV debe contener las columnas 'Nombre' y 'Categoria'.")
        st.stop()

    st.write("Vista previa de los primeros donantes:")
    st.dataframe(df)

    # Permitir seleccionar filas (donantes) del CSV
    indices = df.index.tolist()
    selected_rows = st.multiselect("Selecciona uno o varios donantes:", indices, default=indices[:1])

    if selected_rows:
        # Tomamos el primer donante seleccionado para generar el correo
        donor_row = df.loc[selected_rows[0]]
        selected_donor = donor_row["Nombre"]
        donor_category = donor_row["Categoria"]

        # Función para generar el correo personalizado
        def generate_personalized_email(donor_name, donor_category):
            cat_lower = donor_category.lower()
            if cat_lower == "acquire":
                intent = ("presentar por primera vez la organización y animar al donante a realizar su primera donación")
            elif cat_lower == "returning":
                intent = ("agradecer el apoyo previo y motivar al donante a profundizar su compromiso")
            elif cat_lower == "retention":
                intent = ("apreciar el apoyo continuo y mostrar el impacto para retener su colaboración")
            else:
                intent = ("animar el apoyo del donante de forma respetuosa y personalizada")

            # Instrucción para un correo corto
            # Indicamos en el prompt que el correo sea breve, por ejemplo no más de ~50 palabras.
            # El max_length en el pipeline ayudará a forzar longitud, pero no palabras exactas.
            prompt = (
                f"Eres un recaudador de fondos para una ONG. Escribe un correo electrónico breve (no más de 50 palabras), cálido y sincero para {donor_name}, "
                f"cuyo propósito es {intent}. El correo debe ser en español, amable, agradecido y motivar al donante según su categoría. "
                f"No incluyas marcadores de rol, solo el texto del correo. Debe ser muy corto."
            )
            
            output = replicate.run(
                llm,
                input={
                    "prompt": prompt,
                    "temperature": 0.7,    # Valor fijo
                    "top_p": 0.9,          # Valor fijo
                    "max_length": max_length,
                    "repetition_penalty": 1
                }
            )

            full_response = "".join(output)
            return full_response.strip()

        if st.button("Genera email"):
            with st.spinner("Generando correo..."):
                final_email = generate_personalized_email(selected_donor, donor_category)
            st.markdown("**Correo generado:**")
            st.write(final_email)
    else:
        st.write("Selecciona al menos un donante para generar el correo.")
else:
    st.write("Por favor, sube un archivo CSV para continuar.")
