import streamlit as st

def main():
    # Title of the app
    st.title("Video Game Sentiment Dashboard")

    # Predefined games data
    games = {
        "The Legend of Zelda: Breath of the Wild": {
            "logo_url": "https://upload.wikimedia.org/wikipedia/en/a/a1/The_Legend_of_Zelda_Breath_of_the_Wild.jpg",
            "avg_rating": 9.7,
            "avg_sentiment": 0.85,
        },
        "God of War": {
            "logo_url": "https://upload.wikimedia.org/wikipedia/en/a/a7/God_of_War_4_cover.jpg",
            "avg_rating": 9.6,
            "avg_sentiment": 0.9,
        },
        "Elden Ring": {
            "logo_url": "https://upload.wikimedia.org/wikipedia/en/1/1b/Elden_Ring_Box_art.jpg",
            "avg_rating": 9.5,
            "avg_sentiment": 0.88,
        },
        "Cyberpunk 2077": {
            "logo_url": "https://upload.wikimedia.org/wikipedia/en/9/9f/Cyberpunk_2077_box_art.jpg",
            "avg_rating": 7.8,
            "avg_sentiment": 0.5,
        },
    }

    # Searchbar for game selection
    selected_game = st.text_input("Search for Game Title")

    st.write("---")

    if selected_game:
        # Fetch data for the selected game

        choices = []
        for game in games:
            if selected_game in game:
                choices.append(game)

        if len(choices) > 0:
            selected_game = st.selectbox("Choose Matching Game", list(choices), placeholder="Game")
        else:
            selected_game = None

        if selected_game:
            game_data = games[selected_game]
            st.subheader(selected_game)

            # Display Game Logo
            st.image(game_data["logo_url"], caption=selected_game, use_container_width=True)
            # st.image(S3[f"{game_name}header.jpg"])

            # Display Average Rating
            st.write(f"**Average Rating:** {game_data['avg_rating']} / 10")

            # Display Average Sentiment
            sentiment_description = (
                "Positive" if game_data["avg_sentiment"] > 0 else "Negative" if game_data["avg_sentiment"] < 0 else "Neutral"
            )
            st.write(f"**Average Sentiment:** {game_data['avg_sentiment']} ({sentiment_description})")

if __name__ == "__main__":
    main()
