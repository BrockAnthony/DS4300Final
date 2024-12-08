import boto3
import psycopg2
import json
import numpy as np

def connect_to_db(db_params):
    """Establish a connection to the database."""
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def lambda_handler(event, context):
    # Database credentials
    with open(os.curdir + os.sep + "credentials.json", "r") as f:
        creds = json.load(f)

    db_params = {
        'host': 'reviews.cfim2eisunwi.us-east-2.rds.amazonaws.com',
        'database': 'postgres',
        'user': creds["credentials"]["username"],
        'password': creds["credentials"]["password"]
    }
    
    try:
        # Connect to the database
        conn = connect_to_db(db_params)
        if conn is None:
            print("Failed to connect to the database.")
            return

        cursor = conn.cursor()

        # Fetch changes from the logical replication slot
        cursor.execute("SELECT data FROM pg_logical_slot_get_changes('my_slot', NULL, NULL, 'pretty-print', '1');")
        changes = cursor.fetchall()

        for change in changes:
            print("Change detected:", change[0])  # JSON data
            change_data = json.loads(change[0])

            # Process the changes
            for record in change_data.get("change", []):
                if record["kind"] == "insert" and record["table"] == "game_reviews":
                    # Extract relevant information
                    review_id = next((col for col, val in zip(record["columnnames"], record["columnvalues"]) if col == "review_id"), None)

                    if review_id is not None:
                        # Assign a random score
                        score = np.random.choice([-1, 0, 1])

                        # Update the score for the new review
                        update_query = f"UPDATE game_reviews SET score = {score} WHERE review_id = {review_id};"
                        cursor.execute(update_query)
                        print(f"Updated review_id {review_id} with score {score}.")

        # Commit changes to the database
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
