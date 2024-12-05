import streamlit as st
import pandas as pd

def main():
    # Title of the app
    st.title("Video Game Review Uploader")

    reviews_csv = st.file_uploader("Upload Reviews CSV", type="csv")

    if reviews_csv is not None:
        # Can be used wherever a "file-like" object is accepted:
        df = pd.read_csv(reviews_csv)
        st.write(df)

if __name__ == "__main__":
    main()
