import streamlit as st
import pandas as pd
import psycopg2
import json
import os
import numpy as np
import boto3

def connect_to_db(db_params):
    """Establish a connection to the database."""
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

def write_to_db(conn, df, file_name, review_table="game_reviews", name_table="video_games"):
    """Write the DataFrame to the specified database table."""

    cursor = conn.cursor()

    game_name = file_name.split(".")[0]
    try:
        # insert name
        sql_query = f"INSERT INTO {name_table} (game_name) VALUES ('{game_name}')"
        cursor.execute(sql_query)

        sql_query = f"SELECT game_id FROM {name_table} WHERE game_name = '{game_name}'"
        cursor.execute(sql_query)
        game_id = cursor.fetchone()[0]

        # insert reviews
        for _, row in df.iterrows():
            values = f"{game_id}, '{row['cleaned_review']}', {NULL}}"
            sql_query = f"INSERT INTO {review_table} (game_id, review_text, score) VALUES ({values})"
            cursor.execute(sql_query)

        conn.commit()
        st.success("Data has been successfully written to the database.")
    except Exception as e:
        conn.rollback()
        st.error(f"Error writing to the database: {e}")
    finally:
        cursor.close()

def invoke_lambda(lambda_client, function_name, event):
    """Invoke the Lambda function with a specific event."""
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="Event",  # Asynchronous invocation
            Payload=json.dumps(event)
        )
        if response['StatusCode'] == 202:
            st.success("Lambda function triggered successfully.")
        else:
            st.error(f"Failed to trigger Lambda. Response: {response}")
    except Exception as e:
        st.error(f"Error invoking Lambda function: {e}")


def main():
    with open(os.curdir + os.sep + "credentials.json", "r") as f:
        creds = json.load(f)

    db_params = {
    'host': 'reviews.cfim2eisunwi.us-east-2.rds.amazonaws.com',
    'database': 'postgres',
    'user': creds["credentials"]["username"],
    'password': creds["credentials"]["password"]
    }

    # Title of the app
    st.title("Video Game Review Uploader")

    # AWS Lambda client
    lambda_client = boto3.client('lambda', region_name="us-east-2")  # Adjust region as needed
    lambda_function_name = "onReviewUpload"

    reviews_csv = st.file_uploader("Upload Reviews CSV", type="csv")

    if reviews_csv is not None:
        # Can be used wherever a "file-like" object is accepted:
        df = pd.read_csv(reviews_csv)
        file_name = reviews_csv.name
        st.write(df)

        # Database connection
        conn = connect_to_db(db_params)
        if conn:
            # Trigger Lambda with custom event
            lambda_event = {
                "source": ["aws.ec2"],  # Example source
                "detail-type": ["EC2 Instance State-change Notification"],
                "file_uploaded": file_name,  # Include the file name
                "rows_uploaded": len(df)    # Include metadata about the upload
            }
            invoke_lambda(lambda_client, lambda_function_name, lambda_event)

            # Write data to the database
            write_to_db(conn, df, file_name)
            conn.close()

if __name__ == "__main__":
    main()
