import streamlit as st
import pandas as pd
from openai import OpenAI

# Sidebar for API key input
st.sidebar.title("Configuración")
openai_api_key = st.sidebar.text_input("Clave API de OpenAI", type="password", help="Introduce tu clave API de OpenAI aquí.")

if not openai_api_key:
    st.sidebar.info("Proporciona tu clave API de OpenAI para habilitar la aplicación.", icon="🗝️")

# Main page
st.title("📧 Generador de Correos para Donantes")
st.write(
    "Sube un archivo CSV con información de los donantes y genera correos personalizados seleccionando una fila. "
    "Asegúrate de que el archivo tenga las columnas: `Nombre`, `Recencia` y `Categoria`."
)

# CSV upload section
archivo_cargado = st.file_uploader("Sube tu archivo CSV", type=["csv"], help="Carga un archivo CSV para procesarlo.")
datos = None
if archivo_cargado:
    try:
        # Load the uploaded CSV file
        datos = pd.read_csv(archivo_cargado)
        st.success("¡Archivo CSV cargado exitosamente!")
        st.dataframe(datos, use_container_width=True)
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo: {e}")

if datos is not None:
    # Row selection
    indice_fila = st.number_input(
        "Selecciona un número de fila para generar el correo:",
        min_value=0,
        max_value=len(datos) - 1,
        step=1,
        help="El número de fila corresponde al índice del archivo CSV cargado."
    )
    
    fila_seleccionada = datos.iloc[indice_fila]

    st.write("**Información de la fila seleccionada:**")
    st.write(f"**Nombre:** {fila_seleccionada['Nombre']}")
    st.write(f"**Recencia:** {fila_seleccionada['Recencia']}")
    st.write(f"**Categoría:** {fila_seleccionada['Categoria']}")

    # Optional additional context
    contexto_adicional = st.text_area(
        "Contexto adicional para el correo (opcional):",
        help="Puedes agregar información extra que será incluida en el contexto del correo."
    )

    if openai_api_key:
        client = OpenAI(api_key=openai_api_key)

        if st.button("Generar Correo"):
            # Construct prompt based on row information
            nombre = fila_seleccionada["Nombre"]
            categoria = fila_seleccionada["Categoria"]

            if categoria == "Adquisición":
                prompt = (
                    f"Escribe un correo corto y persuasivo en español dirigido a {nombre}, "
                    "invitándolo a convertirse en donante de nuestra organización. Destaca "
                    "el impacto positivo que tendría su apoyo en nuestras causas, menciona "
                    "los valores que nos impulsan y mantén un tono cálido, cercano y respetuoso."
                )
            elif categoria == "Retención":
                prompt = (
                    f"Escribe un correo corto y amable en español para {nombre}, "
                    "agradeciéndole sinceramente sus donaciones anteriores. "
                    "Invítalo a seguir apoyando nuestras iniciativas, resaltando la "
                    "importancia de su contribución continua y el efecto positivo que "
                    "ha tenido hasta ahora."
                )
            elif categoria == "Recuperación":
                prompt = (
                    f"Escribe un correo corto y cordial en español para {nombre}, "
                    "recordándole nuestra misión y el impacto que su apoyo anterior "
                    "ha tenido. Invítalo a retomar su compromiso como donante, "
                    "destacando cómo su aporte puede ayudar a que sigamos creciendo "
                    "y mejorando."
                )
            else:
                prompt = (
                    f"Escribe un correo corto y general en español para {nombre}, "
                    "invitándolo a apoyar nuestra organización. Destaca brevemente "
                    "nuestra misión, el impacto positivo de su posible donación "
                    "y el valor de su contribución, manteniendo un tono respetuoso y "
                    "cercano."
                )


            # Add additional context if provided
            if contexto_adicional.strip():
                prompt += f" Asegúrate de incluir este contexto adicional: {contexto_adicional.strip()}."

            # Generate response
            with st.spinner("Generando correo..."):
                try:
                    respuesta = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    contenido_correo = respuesta.choices[0].message.content
                    st.subheader("Correo Generado:")
                    st.write(contenido_correo)
                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")
    else:
        st.info("Proporciona tu clave API de OpenAI en la barra lateral para habilitar la generación de correos.", icon="🗝️")
