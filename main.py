import streamlit as st
import pandas as pd

st.title("My First Streamlit App")

st.write("Here's a simple example of a slider:")
value = st.slider("Pick a number", 0, 100, 50)
st.write(f"You selected: {value}")

uploaded_file = st.file_uploader("Upload a CSV file")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Here is the uploaded file:")
    st.write(df)
