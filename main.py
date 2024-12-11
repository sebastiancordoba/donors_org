import streamlit as st
import pandas as pd

st.title("CSV Viewer")

# File uploader in the main area
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    # Display the first 10 rows in the sidebar (left)
    with st.sidebar:
        st.write("First 10 rows of the uploaded CSV:")
        st.dataframe(df.head(10))
else:
    st.write("Please upload a CSV file to display its first 10 rows on the left.")
