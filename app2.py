import streamlit as st
import pandas as pd
import psycopg2
import boto3
import json

# AWS and DB Config (adjust these variables)
AWS_REGION = "us-east-1"
RDS_HOST = "vg-reviews-database.c1w6iqe62olg.us-east-1.rds.amazonaws.com"
RDS_DB = "postgres"
RDS_USER = "username"
RDS_PASSWORD = "0RW14yFmrJ4P9MgW44Bd"

# Connect to RDS PostgreSQL
def connect_db():
    try:
        conn = psycopg2.connect(
            host=RDS_HOST, database=RDS_DB, user=RDS_USER, password=RDS_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        st.error(f"Database connection failed: {e}")
        return None

# Trigger AWS Lambda after review upload
def trigger_lambda(game_title):
    try:
        lambda_client = boto3.client("lambda", region_name=AWS_REGION)
        response = lambda_client.invoke(
            FunctionName="starterSentimentAnalysis",
            InvocationType="Event",
            Payload=json.dumps({"game_title": game_title}),
        )
        return response
    except Exception as e:
        st.error(f"Failed to trigger Lambda: {e}")

# Upload reviews to RDS with dynamic table creation + schema update
def upload_reviews_to_rds(df):
    required_columns = {"title", "cleaned_review"}
    if not required_columns.issubset(df.columns):
        st.error(f"CSV must contain columns: {', '.join(required_columns)}")
        return

    conn = connect_db()
    if conn is None:
        return

    cursor = conn.cursor()
    game_title = df['title'].iloc[0].replace(" ", "_").lower()
    table_name = f"game_reviews_{game_title}"

    try:
        # Create table dynamically if it doesn't exist
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                cleaned_review TEXT NOT NULL,
                sentiment NUMERIC
            )
            """
        )

        # Add sentiment column if missing
        cursor.execute(
            f"""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table_name}' AND column_name = 'sentiment'
                ) THEN
                    ALTER TABLE {table_name} ADD COLUMN sentiment NUMERIC;
                END IF;
            END $$;
            """
        )

        # Insert reviews
        for _, row in df.iterrows():
            cursor.execute(
                f"""
                INSERT INTO {table_name} (title, cleaned_review)
                VALUES (%s, %s)
                """,
                (row["title"], row["cleaned_review"]),
            )

        conn.commit()
        st.success("Reviews uploaded and table updated successfully!")

    except Exception as e:
        st.error(f"Failed to upload reviews: {e}")
    finally:
        conn.close()

# Fetch game data from RDS
# Fetch game data from RDS, including average sentiment
def fetch_game_data(game_title):
    conn = connect_db()
    if conn is None:
        return []

    cursor = conn.cursor()
    table_name = f"game_reviews_{game_title.replace(' ', '_').lower()}"

    try:
        # Fetch unique game title and average sentiment
        cursor.execute(
            f"""
            SELECT DISTINCT title, AVG(sentiment) 
            FROM {table_name}
            WHERE title ILIKE %s
            GROUP BY title
            """,
            (f"%{game_title}%",),
        )
        results = cursor.fetchall()
        return results

    except psycopg2.errors.UndefinedTable:
        st.error(f"No reviews found for '{game_title}'.")
        return []
    except Exception as e:
        st.error(f"Failed to fetch game data: {e}")
        return []
    finally:
        conn.close()

# Main function for Streamlit
def main():
    st.title("Video Game Sentiment Dashboard")

    # Tab Setup
    tab1, tab2 = st.tabs(["Search Games", "Upload Reviews"])

    # Tab 1: Search Games
    with tab1:
        selected_game = st.text_input("Search for Game Title")
        st.write("---")

        if selected_game:
            game_data = fetch_game_data(selected_game)
            if game_data:
                for game_title_tuple in game_data:
                    game_title, avg_sentiment = game_title_tuple 
                    st.subheader(game_title)

                    st.image(
                        f"https://ds4300-logos.s3.us-east-1.amazonaws.com/4300_logos/{game_title.replace(' ', '_').lower()}.jpg",
                        caption=game_title,
                        use_container_width=True,
                    )

                    # Determine sentiment description
                    sentiment_description = (
                        "Positive" if avg_sentiment > 0.5 else 
                        "Neutral" if avg_sentiment == 0 else 
                        "Negative"
                    )

                    # Display average sentiment
                    st.write(f"**Average Sentiment:** {avg_sentiment:.2f} ({sentiment_description})")
        else:
            st.error("No matching games found!")

    # Tab 2: Upload Reviews
    with tab2:
        st.subheader("Upload Game Reviews")
        reviews_csv = st.file_uploader("Upload Reviews CSV", type="csv")

        if reviews_csv is not None:
            df = pd.read_csv(reviews_csv)
            st.write("Uploaded CSV Preview:", df.head())

            if st.button("Upload to RDS"):
                upload_reviews_to_rds(df)

                # Extract game title from the uploaded CSV
                game_title = df['title'].iloc[0].replace(" ", "_").lower()
    
                # Trigger Lambda with the correct game title
                trigger_lambda(game_title)

if __name__ == "__main__":
    main()
