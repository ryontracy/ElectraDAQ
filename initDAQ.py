from sqlalchemy import create_engine, text
import psycopg2
import getpass
import os
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))
daqdbuser = os.environ.get('systemTag')
daqdbuserpassword = os.environ.get('daqdbPassword')

def init_db():
    user = input("Database Admin User Name: ")
    pwd = getpass.getpass("Password: ")
    with open("db_init.sql") as f:
        sql = f.read()
        sql = sql.replace("{user}", f"{daqdbuser}")
        sql = sql.replace("{userpassword}", f"{daqdbuserpassword}")
        print(sql)
        conn = psycopg2.connect(user=user, password=pwd, database='daqdb')
        with conn.cursor() as curs:
            curs.execute(sql)
    conn.close()

    print(user, pwd)

if __name__ == "__main__":
    init_db()