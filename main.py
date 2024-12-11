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
st.set_page_config(page_title="🦙💬 Generador de Correos para Donantes con Llama 2")

with st.sidebar:
    st.title('🦙💬 Generador de Correos para Donantes (Llama 2)')
    if replicate_api:
        st.success('Clave API de Replicate cargada desde config.json', icon='✅')
    else:
        st.warning('No se encontró la clave API en config.json. Por favor agréguela antes de continuar.', icon='⚠️')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    st.subheader('Modelos y parámetros')
    selected_model = st.selectbox('Elige un modelo Llama 2', ['Llama2-7B', 'Llama2-13B'], key='selected_model')
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'

    temperature = st.slider('temperatura (creatividad)', min_value=0.01, max_value=5.0, value=0.7, step=0.01)
    top_p = st.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.slider('longitud máxima del texto', min_value=64, max_value=512, value=256, step=32)
    st.markdown('**Objetivo:** Crear un correo electrónico personalizado para un donante seleccionado, basado en su categoría (acquire, returning, retention). El correo y las respuestas del modelo deben ser en español.')

# Subir el archivo CSV
st.header("Subir la Lista de Donantes")
uploaded_file = st.file_uploader("Sube un archivo CSV que contenga la información de los donantes", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    # Asegurar que las columnas 'name' y 'category' existan
    if "nombre" not in df.columns or "category" not in df.columns:
        st.error("El CSV debe contener las columnas 'nombre' y 'category'.")
        st.stop()

    st.write("Muestra de la lista de donantes:")
    st.dataframe(df.head(10))

    # El usuario selecciona un donante
    donor_names = df["nombre"].unique().tolist()
    selected_donor = st.selectbox("Selecciona un donante:", donor_names)

    # Obtener la fila del donante seleccionado
    donor_row = df[df["nombre"] == selected_donor].iloc[0]
    donor_category = donor_row["category"]

    # Mostrar información del donante seleccionado
    st.write(f"Donante seleccionado: **{selected_donor}** (Categoría: **{donor_category}**)")

    # Estado de la conversación
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "¿En qué puedo ayudarte hoy?"}]

    # Mostrar el historial del chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": "¿En qué puedo ayudarte hoy?"}]
    st.sidebar.button('Borrar historial del chat', on_click=clear_chat_history)

    # Función para generar el correo personalizado
    def generate_personalized_email(donor_name, donor_category):
        # Ajustar el mensaje según la categoría
        # Si la categoría está en inglés, dejamos igual. Si quieres traducir:
        # "acquire" -> "adquisición"
        # "returning" -> "recurrente"
        # "retention" -> "retención"
        # Puedes actualizar el CSV o este código según tus necesidades.
        
        if donor_category.lower() == "acquire":
            intent = ("Presentar por primera vez la organización y animar al donante a realizar su primera donación.")
        elif donor_category.lower() == "returning":
            intent = ("Agradecer al donante por su apoyo previo y motivarlo a profundizar su compromiso.")
        elif donor_category.lower() == "retention":
            intent = ("Apreciar el apoyo continuo del donante y mostrar el impacto de sus contribuciones para retener su apoyo.")
        else:
            intent = ("No se reconoce la categoría. Aun así, escribe un correo respetuoso y personalizado animando su apoyo.")

        prompt = (
            f"Eres un recaudador de fondos para una organización sin fines de lucro. "
            f"Escribe un correo electrónico personalizado, cálido y sincero para {donor_name}, basado en la siguiente intención: {intent} "
            f"El correo debe estar en español, ser amable, agradecido y motivar al donante según su categoría. "
            f"Usa el nombre del donante cuando sea apropiado. "
            f"Termina con un llamado a la acción que se ajuste a la categoría. "
            f"No incluyas ningún marcador de rol como 'Usuario:' o 'Asistente:'. Solo escribe el texto del correo."
        )
        
        output = replicate.run(
            llm,
            input={
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "max_length": max_length,
                "repetition_penalty": 1
            }
        )

        # output es una respuesta en streaming, se debe unir
        full_response = "".join(output)
        return full_response

    # El usuario puede dar instrucciones adicionales
    user_instructions = st.chat_input("Escribe instrucciones adicionales o presiona Enter para generar el correo:")
    if user_instructions:
        st.session_state.messages.append({"role": "user", "content": user_instructions})
        with st.chat_message("user"):
            st.write(user_instructions)

    # Si el último mensaje no es del asistente, generamos el correo ahora
    if (len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] != "assistant") or user_instructions == "":
        with st.chat_message("assistant"):
            with st.spinner("Generando correo personalizado..."):
                # Obtener las instrucciones adicionales (si existen)
                additional_context = st.session_state.messages[-1]["content"] if st.session_state.messages[-1]["role"] == "user" else ""
                
                # Generar el correo
                final_email = generate_personalized_email(selected_donor, donor_category)
                if additional_context.strip():
                    # Si el usuario dio instrucciones extras, las añadimos al final del correo entre corchetes
                    final_email += f"\n\n[Instrucciones adicionales del usuario: {additional_context}]"
                
                st.write(final_email)

        message = {"role": "assistant", "content": final_email}
        st.session_state.messages.append(message)
else:
    st.write("Por favor, sube un archivo CSV para continuar.")
