import re
import os
from flask import Flask
from neo4j import GraphDatabase
from dotenv import load_dotenv
from routers.departments import departments
from routers.workers import workers

app = Flask(__name__)

load_dotenv()

uri = os.getenv('URI')
user = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")

app.register_blueprint(departments)
app.register_blueprint(workers)

if __name__ == "__main__":
    app.run()
