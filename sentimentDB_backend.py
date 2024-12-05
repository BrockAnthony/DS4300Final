import streamlit as st
import pandas as pd

def main():
    # Title of the app
    st.title("Video Game Review Uploader")

    reviews_csv = st.file_uploader("Upload Reviews CSV", type="csv")

    if reviews_csv is not None:
        # To read file as bytes:
        bytes_data = reviews_csv.getvalue()
        st.write(bytes_data)

        # To convert to a string based IO:
        stringio = StringIO(reviews_csv.getvalue().decode("utf-8"))
        st.write(stringio)

        # To read file as string:
        string_data = stringio.read()
        st.write(string_data)

        # Can be used wherever a "file-like" object is accepted:
        dataframe = pd.read_csv(uploaded_file)
        st.write(dataframe)

if __name__ == "__main__":
    main()
