import streamlit as st
import pandas as pd
from openai import OpenAI

# Sidebar for OpenAI API Key
st.sidebar.title("Configuración")
openai_api_key = st.sidebar.text_input("Clave API de OpenAI", type="password", help="Introduce tu clave API de OpenAI aquí.")
if not openai_api_key:
    st.sidebar.info("Proporciona tu clave API de OpenAI para habilitar la generación de correos.", icon="🗝️")

# Main page
st.title("📧 Generador de Correos para Donantes")
st.write(
    "Sube un archivo CSV con información de los donantes para generar correos personalizados o genéricos en función de sus categorías. "
    "Asegúrate de que el archivo tenga las columnas: `Nombre`, `Recencia` y `Categoria`."
)

# CSV Upload
archivo_cargado = st.file_uploader("Sube tu archivo CSV", type=["csv"], help="Carga un archivo CSV para procesarlo.")
datos = None
if archivo_cargado:
    try:
        datos = pd.read_csv(archivo_cargado)
        st.success("¡Archivo CSV cargado exitosamente!")
        st.dataframe(datos, use_container_width=True)
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo: {e}")

if datos is not None:
    # Selection options
    opcion_seleccion = st.radio(
        "Selecciona los donantes para generar correos:",
        ("Seleccionar donantes específicos", "Generar para todos los donantes")
    )

    if opcion_seleccion == "Seleccionar donantes específicos":
        indices_seleccionados = st.multiselect(
            "Selecciona las filas correspondientes a los donantes:",
            options=datos.index,
            format_func=lambda x: f"{datos.loc[x, 'Nombre']} ({datos.loc[x, 'Categoria']})"
        )
        donantes_seleccionados = datos.loc[indices_seleccionados]
    else:
        donantes_seleccionados = datos

    st.write("**Donantes seleccionados para la generación de correos:**")
    st.dataframe(donantes_seleccionados, use_container_width=True)

    # Optional additional context
    contexto_adicional = st.text_area(
        "Contexto adicional para los correos (opcional):",
        help="Puedes agregar información extra que será incluida en el contexto del correo."
    )

    # Personalized or generic emails
    tipo_generacion = st.radio(
        "Selecciona el tipo de correos a generar:",
        ("Personalizados (uno diferente para cada donante)", "Genéricos (uno por categoría con el nombre cambiado)")
    )

    if st.button("Generar Correos"):
        if not openai_api_key:
            st.error("Proporciona tu clave API de OpenAI antes de continuar.")
        elif donantes_seleccionados.empty:
            st.error("No se seleccionaron donantes para la generación.")
        else:
            client = OpenAI(api_key=openai_api_key)
            correos_generados = []
            correos_genericos = {}

            with st.spinner("Generando correos..."):
                try:
                    if tipo_generacion == "Genéricos (uno por categoría con el nombre cambiado)":
                        # Generate generic emails per category
                        categorias = donantes_seleccionados["Categoria"].unique()
                        for categoria in categorias:
                            # Construct prompt for each category
                            if categoria == "Adquisición":
                                prompt = "Escribe un correo corto en español invitando a una persona a ser donante de nuestra organización. Destaca cómo su apoyo puede marcar la diferencia."
                            elif categoria == "Retención":
                                prompt = "Escribe un correo corto en español agradeciendo a una persona por sus donaciones anteriores e invitándola a seguir apoyando nuestra organización."
                            elif categoria == "Recuperación":
                                prompt = "Escribe un correo corto en español recordándole a una persona sobre nuestra organización e invitándola a retomar su apoyo como donante."
                            else:
                                prompt = "Escribe un correo genérico corto en español invitando a una persona a apoyar nuestra organización."

                            # Add additional context if provided
                            if contexto_adicional.strip():
                                prompt += f" Asegúrate de incluir este contexto adicional: {contexto_adicional.strip()}."

                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "user", "content": prompt}],
                            )
                            correos_genericos[categoria] = response.choices[0].message.content

                        # Assign generic emails to donors
                        for _, row in donantes_seleccionados.iterrows():
                            correo = correos_genericos[row["Categoria"]].replace("{nombre}", row["Nombre"])
                            correos_generados.append({
                                "Nombre": row["Nombre"],
                                "Categoria": row["Categoria"],
                                "Contenido del Correo": correo
                            })

                    else:  # Personalized emails
                        for _, row in donantes_seleccionados.iterrows():
                            nombre = row["Nombre"]
                            categoria = row["Categoria"]

                            # Construct prompt based on category
                            if categoria == "Adquisición":
                                prompt = f"Escribe un correo corto en español para {nombre} invitándolo a ser donante de nuestra organización. Destaca cómo su apoyo puede marcar la diferencia."
                            elif categoria == "Retención":
                                prompt = f"Escribe un correo corto en español para {nombre} agradeciéndole por sus donaciones anteriores e invitándolo a seguir apoyando nuestra organización."
                            elif categoria == "Recuperación":
                                prompt = f"Escribe un correo corto en español para {nombre} recordándole sobre nuestra organización e invitándolo a retomar su apoyo como donante."
                            else:
                                prompt = f"Escribe un correo genérico corto en español para {nombre} invitándolo a apoyar nuestra organización."

                            # Add additional context if provided
                            if contexto_adicional.strip():
                                prompt += f" Asegúrate de incluir este contexto adicional: {contexto_adicional.strip()}."

                            # Generate email content
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "user", "content": prompt}],
                            )
                            email_content = response.choices[0].message.content

                            correos_generados.append({
                                "Nombre": nombre,
                                "Categoria": categoria,
                                "Contenido del Correo": email_content
                            })

                    st.success("¡Los correos han sido generados exitosamente!")
                    st.write("Correos generados:")
                    st.dataframe(pd.DataFrame(correos_generados))
                except Exception as e:
                    st.error(f"Ocurrió un error al generar los correos: {e}")
