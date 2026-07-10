import boto3
import pymysql
import os
import json

def lambda_handler(event, context):
    secret_name = os.environ['SECRET_NAME']
    database = os.environ['DB_NAME']

    # Recuperar el secreto de Secrets Manager
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])

    host = secret['host']
    user = secret['username']
    password = secret['password']

    connection = None
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=database,
            connect_timeout=5
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM alumnos;")  
            results = cursor.fetchall()

        return {
            "statusCode": 200,
            "body": results
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "error": str(e)
        }

    finally:
        if connection:
            connection.close()
