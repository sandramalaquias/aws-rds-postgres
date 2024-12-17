import boto3
import json
import os
import pandas as pd
import requests
import psycopg2

boto3_session = boto3.session.Session()
s3_client = boto3_session.client("s3")

def getDataURL():

    # API URL
    url = "https://olinda.mec.gov.br/olinda-ide/servico/PDA_SETEC/versao/v1/odata/Regulacao_Cursos"

    # Requests get Data
    response = requests.get(url)

    # Check status
    if response.status_code == 200:
        data = response.json()  # Converte para dicionário Python

        # Convert to pandas datafraee
        df = pd.DataFrame(data["value"])

    else:
        raise RuntimeError(f"Error to get Data via API {url} - {response}, {response.raise_for_status()}, {response.reason}")

    return df


def getDataLocal():
    df = pd.read_csv('../Regulacao_Cursos.csv', encoding='UTF-8')

    # path to RDS credentials
    file_path = "../rds.json"

    with open(file_path, "r") as file:
        rds = json.load(file)

    db_config = {
    "dbname": rds['RDS_DB_NAME'],
    "user": rds['RDS_USER'],
    "password": rds['RDS_PASSWORD'],
    "host": rds['RDS_ENDPOINT'].split(":")[0],
    "port": rds['RDS_PORT'],
}
    return df, db_config

def newCols(df, df_state):
    df.drop_duplicates(inplace=True)

    # normalize int dtypes
    df['CODIGO_CURSO'] = df['CODIGO_CURSO'].astype(int)
    df['CARGA_HORARIA_CURSO'] = df['CARGA_HORARIA_CURSO'].astype(int)
    df['CODIGO_UNIDADE_DE_ENSINO'] = df['CODIGO_UNIDADE_DE_ENSINO'].astype(int)
    df['CODIGO_MUNICIPIO'] = df['CODIGO_MUNICIPIO'].astype(int)

    # workload minimum
    group_col = ['CODIGO_CURSO']
    df['CARGA_HORARIA_MINIMA'] = df.groupby(group_col)['CARGA_HORARIA_CURSO'].transform('min')

    # refatoring STATUS_ATIVO
    df['STATUS'] = 'não'  # default
    df['STATUS'] = df['STATUS'].where(df['SITUACAO_ATIVO'] == 't', 'sim')

    #complete with state data
    df = df.merge(df_state[['state_flag', 'state_ibge', 'state_name']], left_on='UF', right_on='state_flag', how='inner')

    # Normalizing 'UNIDADE_DE_ENSINO'
    df['UNIDADE_DE_ENSINO_NORM'] = df['UNIDADE_DE_ENSINO'].apply(
    lambda school: school.replace("\\", '').replace("'", "’").upper() if "'" in school or "\\" in school else school.upper())

    return df

def courseType(df, cur):

    if len(df['NOME_SUBTIPO_DE_CURSOS'].unique())== 1:
        values = df['NOME_SUBTIPO_DE_CURSOS'].unique()[0]
    else:
       list_values = (x for x in df['NOME_SUBTIPO_DE_CURSOS'].unique())
       result = tuple((x,) for x in list_values)
       values = str(result).replace(',)',')').replace('((', '').replace('))', '')

    # Define the SQL INSERT query with ON CONFLICT DO UPDATE and RETURNING
    table_insert = f"""
    INSERT INTO course_type (name)
    VALUES ('{values}')
    ON CONFLICT (name) DO UPDATE
    SET name = EXCLUDED.name
    RETURNING name, course_type_pk;
    """

    cur.execute(table_insert)

    # Convert the query result to DataFrame
    query_results = cur.fetchall()
    result_df = pd.DataFrame(query_results, columns=["NOME_SUBTIPO_DE_CURSOS", "course_type_pk"])

    # Update the original DataFrame with ID's
    df = df.merge(result_df, on="NOME_SUBTIPO_DE_CURSOS", how="inner")

    return df


def getState():
    state_list = [[11,'RO','Rondônia','rondonia','N','Norte','norte'],
    [12,'AC','Acre','acre','N','Norte','norte'],
    [13,'AM','Amazonas','amazonas','N','Norte','norte'],
    [14,'RR','Roraima','roraima','N','Norte','norte'],
    [15,'PA','Pará','para','N','Norte','norte'],
    [16,'AP','Amapá','amapa','N','Norte','norte'],
    [17,'TO','Tocantins','tocantins','N','Norte','norte'],
    [21,'MA','Maranhão','maranhao','NE','Nordeste','nordeste'],
    [22,'PI','Piauí','piaui','NE','Nordeste','nordeste'],
    [23,'CE','Ceará','ceara','NE','Nordeste','nordeste'],
    [24,'RN','Rio Grande do Norte','riograndedonorte','NE','Nordeste','nordeste'],
    [25,'PB','Paraíba','paraiba','NE','Nordeste','nordeste'],
    [26,'PE','Pernambuco','pernambuco','NE','Nordeste','nordeste'],
    [27,'AL','Alagoas','alagoas','NE','Nordeste','nordeste'],
    [28,'SE','Sergipe','sergipe','NE','Nordeste','nordeste'],
    [29,'BA','Bahia','bahia','NE','Nordeste','nordeste'],
    [31,'MG','Minas Gerais','minasgerais','SE','Sudeste','sudeste'],
    [32,'ES','Espírito Santo','espiritosanto','SE','Sudeste','sudeste'],
    [33,'RJ','Rio de Janeiro','riodejaneiro','SE','Sudeste','sudeste'],
    [35,'SP','São Paulo','saopaulo','SE','Sudeste','sudeste'],
    [41,'PR','Paraná','parana','S','Sul','sul'],
    [42,'SC','Santa Catarina','santacatarina','S','Sul','sul'],
    [43,'RS','Rio Grande do Sul','riograndedosul','S','Sul','sul'],
    [50,'MS','Mato Grosso do Sul','matogrossodosul','CO','Centro-Oeste','centrooeste'],
    [51,'MT','Mato Grosso','matogrosso','CO','Centro-Oeste','centrooeste'],
    [52,'GO','Goiás','goias','CO','Centro-Oeste','centrooeste'],
    [53,'DF','Distrito Federal','distritofederal','CO','Centro-Oeste','centrooeste']]

    state_columns = ["state_ibge","state_flag", "state_name", "state_name_norm", "region_flag", "region_name", "region_name_norm"]

    df_state = df = pd.DataFrame(state_list, columns=state_columns)
    df_state = df_state[['state_flag', 'state_ibge', 'state_name']]

    return df_state

def axisTech(df, cur):

    if len(df['EIXO_TECNOLOGICO'].unique())== 1:
        values = df['EIXO_TECNOLOGICO'].unique()[0]
    else:
       list_values = (x for x in df['EIXO_TECNOLOGICO'].unique())
       result = tuple((x,) for x in list_values)
       values = str(result).replace(',)',')').replace('((', '').replace('))', '')


    # Define the SQL INSERT query with ON CONFLICT DO UPDATE and RETURNING
    table_insert = f"""
    INSERT INTO tech_axis (name)
    VALUES ({values})
    ON CONFLICT (name) DO UPDATE
    SET name = EXCLUDED.name
    RETURNING name, tech_axis_pk;
    """

    cur.execute(table_insert)

    # Convert the query result to DataFrame
    query_results = cur.fetchall()
    result_df = pd.DataFrame(query_results, columns=["EIXO_TECNOLOGICO", "tech_axis_pk"])

    # Update the original DataFrame with ID's
    df = df.merge(result_df, on="EIXO_TECNOLOGICO", how="inner")

    return df

def modal(df, cur):

    if len(df['MODALIDADE'].unique())== 1:
        values = df['MODALIDADE'].unique()[0]
    else:
       list_values = (x for x in df['MODALIDADE'].unique())
       result = tuple((x,) for x in list_values)
       values = str(result).replace(',)',')').replace('((', '').replace('))', '')


    # Define the SQL INSERT query with ON CONFLICT DO UPDATE and RETURNING
    table_insert = f"""
    INSERT INTO modal (name)
    VALUES ({values})
    ON CONFLICT (name) DO UPDATE
    SET name = EXCLUDED.name
    RETURNING name, modal_pk;
    """

    cur.execute(table_insert)

    # Convert the query result to DataFrame
    query_results = cur.fetchall()
    result_df = pd.DataFrame(query_results, columns=["MODALIDADE", "modal_pk"])

    # Update the original DataFrame with ID's
    df = df.merge(result_df, on="MODALIDADE", how="inner")

    return df

def state(df, cur):
    list_col = ['state_flag', 'state_ibge', 'state_name']
    list_of_tuples = list(df[list_col].drop_duplicates().itertuples(index=False, name=None))
    values = str(list_of_tuples).replace('[', '').replace(']', '')

    # Define the SQL INSERT query with ON CONFLICT DO UPDATE and RETURNING
    table_insert = f"""
    INSERT INTO state (cod_uf, cod_ibge, name)
    VALUES {values}
    ON CONFLICT (cod_uf) DO UPDATE
    SET cod_uf = EXCLUDED.cod_uf
    RETURNING cod_uf, state_pk;
    """

    cur.execute(table_insert)

    # Convert the query result to DataFrame
    query_results = cur.fetchall()
    result_df = pd.DataFrame(query_results, columns=["state_flag", "state_pk"])

    # Update the original DataFrame with ID's
    df = df.merge(result_df, on="state_flag", how="inner")

    return df

def city(df, cur):

    list_col = ['CODIGO_MUNICIPIO', 'MUNICIPIO', 'state_pk']
    list_of_tuples = list(df[list_col].drop_duplicates().itertuples(index=False, name=None))
    values = str(list_of_tuples).replace('[', '').replace(']', '')

    # Define the SQL INSERT query with ON CONFLICT DO UPDATE and RETURNING
    table_insert = f"""
    INSERT INTO city (cod_ibge, name, state_fk)
    VALUES {values}
    ON CONFLICT (cod_ibge) DO UPDATE
    SET cod_ibge = EXCLUDED.cod_ibge
    RETURNING cod_ibge, city_pk;
    """

    cur.execute(table_insert)

    # Convert the query result to DataFrame
    query_results = cur.fetchall()
    result_df = pd.DataFrame(query_results, columns=["CODIGO_MUNICIPIO", "city_pk"])

    # Update the original DataFrame with ID's
    df = df.merge(result_df, on="CODIGO_MUNICIPIO", how="inner")

    return df

def course(df,cur):

    list_col = ['CODIGO_CURSO', 'CURSO', 'CARGA_HORARIA_MINIMA', 'tech_axis_pk', 'course_type_pk']

    list_of_tuples = list(df[list_col].drop_duplicates().itertuples(index=False, name=None))
    values = str(list_of_tuples).replace('[', '').replace(']', '')

    # Define the SQL INSERT query with ON CONFLICT DO UPDATE and RETURNING
    table_insert = f"""
    INSERT INTO course (cod_course, name, min_workload, tech_axis_fk, course_type_fk)
    VALUES {values}
    ON CONFLICT (cod_course) DO UPDATE
    SET cod_course = EXCLUDED.cod_course
    RETURNING cod_course, course_pk;
    """

    cur.execute(table_insert)

    # Convert the query result to DataFrame
    query_results = cur.fetchall()
    result_df = pd.DataFrame(query_results, columns=["CODIGO_CURSO", "course_pk"])

    # Update the original DataFrame with ID's
    df = df.merge(result_df, on="CODIGO_CURSO", how="inner")

    return df

def schools(df,cur):

    list_col = ['UNIDADE_DE_ENSINO_NORM', 'city_pk', 'CODIGO_UNIDADE_DE_ENSINO']

    list_of_tuples = list(df[list_col].drop_duplicates().itertuples(index=False, name=None))
    values = str(list_of_tuples).replace('[', '').replace(']', '')

    # Define the SQL INSERT query with ON CONFLICT DO UPDATE and RETURNING
    table_insert = f"""
    INSERT INTO schools (name, city_fk, unit_cod)
    VALUES {values}
    ON CONFLICT (unit_cod) DO UPDATE
    SET unit_cod = EXCLUDED.unit_cod
    RETURNING unit_cod, schools_pk;
    """

    cur.execute(table_insert)

    # Convert the query result to DataFrame
    query_results = cur.fetchall()
    result_df = pd.DataFrame(query_results, columns=["CODIGO_UNIDADE_DE_ENSINO", "school_pk"])

    # Update the original DataFrame with ID's
    df = df.merge(result_df, on="CODIGO_UNIDADE_DE_ENSINO", how="inner")

    return df

def course_school(df,cur):

    list_col = ['school_pk', 'course_pk', 'modal_pk', 'CARGA_HORARIA_CURSO', 'STATUS']

    list_of_tuples = list(df[list_col].drop_duplicates().itertuples(index=False, name=None))
    values = str(list_of_tuples).replace('[', '').replace(']', '')

    # Define the SQL INSERT query with ON CONFLICT DO UPDATE and RETURNING
    table_insert = f"""
    INSERT INTO course_school(school_fk, course_fk, modal_fk, local_workload, status)
    VALUES {values}
    ON CONFLICT ON CONSTRAINT unique_course_school
    DO UPDATE
    SET local_workload = EXCLUDED.local_workload,
        status = EXCLUDED.status
    RETURNING course_school_pk, school_fk, course_fk, modal_fk;
    """

    cur.execute(table_insert)

    # Convert the query result to DataFrame
    query_results = cur.fetchall()
    result_df = pd.DataFrame(query_results, columns=['course_school_pk', 'school_pk', 'course_pk', 'modal_pk'])

    # Update de dataframe with course_school_pk
    df = df.merge(result_df, on=['school_pk', 'course_pk', 'modal_pk'], how='inner')

    return df

## Pipeline
def pipeline(db_config, df):
    print ('start Load')
    df_state = getState()
    df = newCols(df, df_state)

    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    df = courseType(df, cur)
    print ('course_type loaded')

    df = axisTech(df, cur)
    print ('tech_axis loaded')

    df = modal(df, cur)
    print ('modal loaded')

    df = state(df, cur)
    print ('state loaded')

    df = city(df, cur)
    print ('city loaded')

    df = course(df, cur)
    print ('course loaded')

    df = schools(df, cur)
    print ('schools loaded')

    df = course_school(df, cur)
    print ('course_school loaded')

    conn.commit()
    conn.close()


