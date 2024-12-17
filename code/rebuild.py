import boto3
import os
import json
import psycopg2

from ddlSQL import *

boto3_session = boto3.session.Session()
s3_client = boto3_session.client("s3")

#get endpoint for RDS

def getRDS():
    bucket_name = os.getenv('BUCKET_NAME')
    file_key = os.getenv('RDS_JSON')

    if not (bucket_name or file_key):
        raise RuntimeError(f"bucket_name e key credentials not found")

    try:
       response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
       content = response["Body"].read().decode("utf-8")
       rds = json.loads(content)

    except Exception as e:
        raise RuntimeError(f"Error in read file on AWS S3: file {file_key} do bucket {bucket_name}: {str(e)}")

    db_config = {
    "dbname": rds['RDS_DB_NAME'],
    "user": rds['RDS_USER'],
    "password": rds['RDS_PASSWORD'],
    "host": rds['RDS_ENDPOINT'].split(":")[0],
    "port": rds['RDS_PORT'],
}
    return db_config


def rebuildTables(db_config):
    conn = psycopg2.connect(**db_config)
    conn.set_session(autocommit=True)
    cur = conn.cursor()

    #database rebuild
    for ddl in drop_table:
        try:
            cur.execute(ddl)
        except Exception as e:
            raise RuntimeError(f"Error in drop table: {str(e)} - {ddl}")

    print ("Drop Tables")

    for ddl in new_tables:
        try:
            cur.execute(ddl)
        except Exception as e:
            raise RuntimeError(f"Error in create table: {str(e)} {ddl}")

    print ('New Tables')
    conn.close()