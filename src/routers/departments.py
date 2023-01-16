from flask import Blueprint, jsonify
from main import driver

departments = Blueprint('departments', __name__)


def getDepartments(tx, sort: str = '', sortType: str = '', filter: str = '', filterType: str = ''):
    query = "MATCH (m:Department) RETURN m"
    if (sortType == 'asc'):
        if (sort == 'name'):
            query = "MATCH (m:Department) RETURN m ORDER BY m.name"
        if (sort == 'numberOfEmployees'):
            query = f"""MATCH 
               (m:Employee)-[r:WORKS_IN]-(d:Department)
               RETURN d.name ORDER BY count(m)"""
    if (sortType == 'desc'):
        if (sort == 'name'):
            query = "MATCH (m:Department) RETURN m ORDER BY m.name DESC"
        if (sort == 'numberOfEmployees'):
            query = f"""MATCH 
               (m:Employee)-[r:WORKS_IN]-(d:Department)
               RETURN d.name ORDER BY count(m) DESC"""
    if (filterType == 'name'):
        query = f"MATCH (m:Department) WHERE m.name CONTAINS '{filtr}' RETURN m"
    if (filterType == 'numberOfEmployees'):
        query = f"""MATCH 
               (m:Employee)-[r:WORKS_IN]-(d:Department)
               WHERE count(m) = '{filter}'               
               RETURN d.name"""
    results = tx.run(query).data()
    departments = [{'name': result['m']['name']} for result in results]
    return departments


@departments.route('/departments', methods=['GET'])
def get_departments_route():
    with driver.session() as session:
        departments = session.read_transaction(getDepartments)
    res = {'departments': departments}
    return jsonify(res)


def getDepartmentsEmployees(tx, name: str):
    query = f"MATCH (m:Employee)-[r:WORKS_IN]-(d:Department {{name:'{name}'}}) RETURN m"
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'], 'surname': result['m']
                ['surname'], 'position': result['m']['position']} for result in results]
    return workers


@departments.route('/departments/<string:name>/employees', methods=['GET'])
def getDepartmentRouteFromDepartment(name: str):
    with driver.session() as session:
        workers = session.execute_read(getDepartmentsEmployees, name)
    res = {'workers': workers}
    return jsonify(res)
