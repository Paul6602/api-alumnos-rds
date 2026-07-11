import boto3
import pymysql
import random
import string
import json

def generar_password(longitud=12):
    # Genera una clave segura compatible con MySQL
    caracteres = string.ascii_letters + string.digits + "!#%^&*"
    return ''.join(random.choice(caracteres) for i in range(longitud))

def lambda_handler(event, context):
    # Clientes de AWS
    ssm = boto3.client('ssm')
    secrets_client = boto3.client('secretsmanager')

    # Credenciales de administrador (hardcodeadas para el lab, en prod irían en un secreto)
    host = 'alumnos.colnz8yz1ufz.us-east-1.rds.amazonaws.com'
    admin_user = 'admin'
    admin_password = 'MiClaveSegura123'
    entornos = ['dev', 'test', 'prod']

    try:
        # 1. Conexión a MySQL como administrador
        connection = pymysql.connect(
            host=host,
            user=admin_user,
            password=admin_password,
            autocommit=True # Crucial para que los cambios de usuario se guarden
        )

        with connection.cursor() as cursor:
            for env in entornos:
                nuevo_pass = generar_password()
                db_user = f"user_{env}"

                # A. Actualizar contraseña en MySQL
                cursor.execute(f"ALTER USER '{db_user}'@'%' IDENTIFIED BY '{nuevo_pass}';")

                # B. Actualizar en Systems Manager - Parameter Store (Requisito Ejercicio 2)
                param_name = f"/rds_mysql_alumnos/{db_user}/password"
                ssm.put_parameter(
                    Name=param_name,
                    Value=nuevo_pass,
                    Type='SecureString',
                    Overwrite=True
                )

                # C. Actualizar en Secrets Manager (Para que tu API del Ejercicio 1 no se caiga)
                secret_name = f"rds/alumnos/{env}"
                current_secret = secrets_client.get_secret_value(SecretId=secret_name)
                secret_dict = json.loads(current_secret['SecretString'])
                secret_dict['password'] = nuevo_pass
                
                secrets_client.put_secret_value(
                    SecretId=secret_name,
                    SecretString=json.dumps(secret_dict)
                )

                print(f"Clave rotada con éxito para {db_user}")

        return {
            "statusCode": 200,
            "body": "Rotación de secretos completada exitosamente en todos los entornos."
        }

    except Exception as e:
        print(f"Error durante la rotación: {str(e)}")
        return {
            "statusCode": 500,
            "error": str(e)
        }
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()