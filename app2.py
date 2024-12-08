import streamlit as st
import pandas as pd
import psycopg2
import json
import os
import boto3

# Database connection
def connect_to_db(db_params):
    """Establish a connection to the database."""
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

# Fetch game details
def fetch_game_data(conn, game_title):
    """Fetch game reviews and sentiment score."""
    cursor = conn.cursor()
    try:
        query = f"""
        SELECT v.game_name, r.review_text, r.score
        FROM video_games v
        JOIN game_reviews r ON v.game_id = r.game_id
        WHERE LOWER(v.game_name) LIKE LOWER(%s)
        """
        cursor.execute(query, (f"%{game_title}%",))
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching game data: {e}")
        return []
    finally:
        cursor.close()

# Write reviews to DB
def write_to_db(conn, df, game_title):
    """Insert game and review data into the database."""
    cursor = conn.cursor()
    try:
        cursor.execute(f"INSERT INTO video_games (game_name) VALUES (%s) ON CONFLICT DO NOTHING", (game_title,))
        cursor.execute(f"SELECT game_id FROM video_games WHERE game_name = %s", (game_title,))
        game_id = cursor.fetchone()[0]

        for _, row in df.iterrows():
            review_text = row['cleaned_review']
            cursor.execute(
                "INSERT INTO game_reviews (game_id, review_text, score) VALUES (%s, %s, NULL)",
                (game_id, review_text)
            )
        conn.commit()
        st.success("Data successfully written to the database.")
    except Exception as e:
        conn.rollback()
        st.error(f"Error writing to the database: {e}")
    finally:
        cursor.close()

# Trigger AWS Lambda function
def trigger_lambda(game_title):
    """Trigger AWS Lambda function."""
    lambda_client = boto3.client('lambda', region_name="us-east-2")
    lambda_function_name = "onReviewUpload"
    event = {
        "file_uploaded": game_title,
        "source": "web_app",
        "detail-type": "Game Review Upload"
    }
    try:
        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="Event",
            Payload=json.dumps(event)
        )
        if response['StatusCode'] == 202:
            st.success("Lambda function triggered successfully.")
        else:
            st.error("Failed to trigger Lambda function.")
    except Exception as e:
        st.error(f"Error invoking Lambda function: {e}")

# Main function
def main():
    with open("credentials.json", "r") as f:
        creds = json.load(f)

    db_params = {
        'host': 'reviews.cfim2eisunwi.us-east-2.rds.amazonaws.com',
        'database': 'postgres',
        'user': creds["credentials"]["username"],
        'password': creds["credentials"]["password"]
    }

    st.title("Video Game Sentiment Dashboard")

    # Tab Setup
    tab1, tab2 = st.tabs(["Search Games", "Upload Reviews"])

    # Tab 1: Search Games (Fetch RDS Data; Display Video Game Data + Logo)
    with tab1:
        st.subheader("Search Games by Title")
        selected_game = st.text_input("Enter Game Title")

        if selected_game:
            conn = connect_to_db(db_params)
            cursor = conn.cursor()
            sql_query = f"SELECT game_name FROM video_games;"
            cursor.execute(sql_query)
            games = cursor.fetchall()

            choices = []
            for game in games:
                game = game[0][:-8]
                if selected_game in game:
                    choices.append(game)

            if len(choices) > 0:
                selected_game = st.selectbox("Choose Matching Game", list(choices), placeholder="Game")
            else:
                st.write("No games with search term.")
                selected_game = None

            if selected_game:
                if conn:
                    game_data = fetch_game_data(conn, selected_game)
                    conn.close()

                    if game_data:
                        st.subheader(f"Results for '{selected_game}'")

                        # Create DataFrame for search results
                        df = pd.DataFrame(game_data, columns=["Game Title", "Review Text", "Sentiment Score"])
                        avg_sentiment = df["Sentiment Score"].mean()

                        # Determine sentiment description
                        sentiment_description = (
                            "Positive" if avg_sentiment > 0.05 else
                            "Neutral" if avg_sentiment == 0 else
                            "Negative"
                        )

                        # Display sentiment and reviews
                        st.write(f"**Average Sentiment:** {avg_sentiment:.2f} ({sentiment_description})")

                        # Display game logo from S3 bucket
                        game_logo_url = f"https://ds4300-logos.s3.us-east-1.amazonaws.com/4300_logos/{selected_game.replace(' ', '_').lower()}.jpg"

                        st.image(
                            game_logo_url,
                            caption=selected_game.title(),  # Proper title formatting
                            use_container_width=True,
                        )

                        # Show game review DataFrame
                        st.dataframe(df)
                    else:
                        st.error("No matching games found!")

    # Tab 2: Upload Reviews (Upload to RDS/Trigger Lambda)
    with tab2:
        st.subheader("Upload Game Reviews")
        reviews_csv = st.file_uploader("Upload Reviews CSV", type="csv")

        if reviews_csv is not None:
            df = pd.read_csv(reviews_csv)
            st.write("Uploaded CSV Preview:", df.head())

            if st.button("Upload to RDS"):
                game_title = reviews_csv.name.replace(".csv", "").replace("_", " ").title()
                conn = connect_to_db(db_params)
                if conn:
                    write_to_db(conn, df, game_title)
                    conn.close()
                    trigger_lambda(game_title)

if __name__ == "__main__":
    main()
