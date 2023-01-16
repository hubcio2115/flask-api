from flask import Blueprint, request, jsonify

workers = Blueprint('departments', __name__)


def getWorkers(tx, sort: str = '', sortType: str = '', filter: str = '', filterType: str = ''):
    query = "MATCH (m:Employee) RETURN m"
    if (sortType == 'asc'):
        if (sort == 'name'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.name"
        elif (sort == 'surname'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.surname"
        elif (sort == 'position'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.position"
    if (sortType == 'desc'):
        if (sort == 'name'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.name DESC"
        elif (sort == 'surname'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.surname DESC"
        elif (sort == 'position'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.position DESC"
    if (filterType == 'name'):
        query = f"MATCH (m:Employee) WHERE m.name CONTAINS '{filter}' RETURN m"
    if (filterType == 'surname'):
        query = f"MATCH (m:Employee) WHERE m.surname CONTAINS '{filter}' RETURN m"
    if (filterType == 'position'):
        query = f"MATCH (m:Employee) WHERE m.position CONTAINS '{filter}' RETURN m"
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'],
               'surname': result['m']['surname']} for result in results]
    return workers


@workers.route('/employees', methods=['GET'])
def getWorkersRoute():
    args = request.args
    sort = args.get("sort")
    sortType = args.get("sortType")
    filter = args.get("filter")
    filterType = args.get("filterType")
    with driver.session() as session:
        workers = session.execute_read(
            getWorkers, sort, sortType, filter, filterType)
    res = {'workers': workers}
    return jsonify(res)


def getWorkersSubordinates(tx, name: str, surname: str):
    query = f"""MATCH (p:Employee), (p1:Employee {{name:'{name}', surname:'{surname}'}})-[r]-(d)
               WHERE NOT (p)-[:MANAGES]-(:Department)
               AND (p)-[:WORKS_IN]-(:Department {{name:d.name}})
               RETURN p"""
    results = tx.run(query).data()
    workers = [{'name': result['p']['name'],
               'surname': result['p']['surname']} for result in results[:len(results)//2]]
    return workers


@workers.route('/employees/<person>/subordinates', methods=['GET'])
def getWorkersSubordinatesRoute(person):
    person1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person1[0]
    surname = person1[1]
    with driver.session() as session:
        workers = session.read_transaction(
            get_workers_subordinates, name, surname)
    res = {'workers': workers}
    return jsonify(res)


def getDepartmentsFromEmployees(tx, name: str, surname: str):
    query = f"""MATCH 
               (m:Employee {{name:'{name}', surname:'{surname}'}})-[r:WORKS_IN]-(d:Department), 
               (m1:Employee)-[r1:MANAGES]-(d1:Department {{name:d.name}}),
               (m2:Employee)-[r2:WORKS_IN]-(d2:Department {{name:d.name}}) 
               RETURN d.name AS name, m1.name AS Manager, count(m2) AS Number_of_Employees"""
    result = tx.run(query).data()
    departments = [{'Name': result[0]['name'], 'Manager': result[0]
                    ['Manager'], 'Number of employees':result[0]['Number_of_Employees']+1}]
    return departments


@workers.route('/employees/<string:person>/department', methods=['GET'])
def get_departments_route_from_employee(person):
    person1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person1[0]
    surname = person1[1]
    with driver.session() as session:
        departments = session.read_transaction(
            getDepartmentsFromEmployees, name, surname)
    res = {'department': departments}
    return jsonify(res)


def addWorker(tx, name: str, surname: str, position: str, department: str):
    query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' AND m.position='{position}' RETURN m"
    result = tx.run(query, name=name).data()
    if not result:
        query = f"CREATE ({name}:Employee {{name:'{name}', surname:'{surname}', position:'{position}'}})"
        query2 = f"MATCH (a:Employee),(b:Department) WHERE a.name = '{name}' AND a.surname = '{surname}' AND b.name = '{department}' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)"
        tx.run(query, name=name, surname=surname, position=position)
        tx.run(query2, name=name, surname=surname, department=department)
    else:
        return 'Person exist'


@workers.route('/employees', methods=['POST'])
def addWorkerRoute():
    name = request.form['name']
    surname = request.form['surname']
    position = request.form['position']
    department = request.form['department']
    if (name == '' or surname == '' or position == '' or department == ''):
        return 'Not a complete request'

    with driver.session() as session:
        session.execute_write(addWorker, name, surname, position, department)

    res = {'status': 'success'}
    return jsonify(res)


def updateWorker(tx, name: str, surname: str, new_name: str, new_surname: str, new_department: str, new_position: str):
    query = f"MATCH (m:Employee)-[r]-(d:Department) WHERE m.name='{name}' AND m.surname='{surname}' RETURN m,d,r"
    res = tx.run(query, name=name, surname=surname).data()
    print(res)
    print(res[1]['r'][1])
    if not res:
        return None
    else:
        query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' SET m.name='{new_name}', m.surname='{new_surname}', m.position='${new_position}'"
        query1 = f"MATCH (m:Employee {{name: '{name}', surname: '{surname}'}})-[r:WORKS_IN]->(d:Department {{name:'{res[0]['d']['name']}'}}) DELETE r"
        query2 = f"""MATCH (a:Employee),(b:Department) WHERE a.name = '{name}' AND a.surname = '{surname}' AND b.name = '{new_department}' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)"""
        tx.run(query, name=name, surname=surname, new_name=new_name,
               new_surname=new_surname, new_position=new_position)
        tx.run(query1, name=name, surname=surname)
        tx.run(query2, name=name, surname=surname,
               new_department=new_department)
        return {'name': new_name, 'surname': new_surname, 'position': new_position, 'New department': new_department}


@workers.route('/employees/<string:person>', methods=['PUT'])
def updateWorkerRoute(person):
    person1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person1[0]
    surname = person1[1]
    new_name = request.form['name']
    new_surname = request.form['surname']
    new_department = request.form['department']
    new_position = request.form['position']

    with driver.session() as session:
        worker = session.write_transaction(
            updateWorker, name, surname, new_name, new_surname, new_department, new_position)

    if not worker:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)


def deleteWorker(tx, name: str, surname: str):
    query = f"MATCH (m:Employee)-[r]-(d:Department) WHERE m.name='{name}' AND m.surname='{surname}' RETURN m,d,r"
    res = tx.run(query, name=name, surname=surname).data()
    if not res:
        return None
    else:
        query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' DETACH DELETE m"
        tx.run(query, name=name, surname=surname)
        if (len(res) > 1):
            query = f"MATCH (m:Employee)-[r:WORKS_IN]-(d:Department {{name:'{res[0]['d']['name']}'}}) RETURN m"
            results = tx.run(query).data()
            if (len(results) == 0):
                query = f"MATCH (d:Department) WHERE d.name='{res[0]['d']['name']}' DETACH DELETE d"
                tx.run(query, name=name, surname=surname)
            workers = [{'name': res['m']['name'], 'surname': res['m']
                        ['surname'], 'position': res['m']['position']} for res in results]
            query2 = f"""MATCH (a:Employee),(b:Department) WHERE a.name = '{workers[0]['name']}' AND a.surname = '{workers[0]['surname']}' AND b.name = '{res[0]['d']['name']}' CREATE (a)-[r:MANAGES]->(b) RETURN type(r)"""
            tx.run(query2)
        return {'name': name, 'surname': surname}


@workers.route('/employees/<string:person>', methods=['DELETE'])
def deleteWorkerRoute(person):
    person1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person1[0]
    surname = person1[1]
    with driver.session() as session:
        worker = session.write_transaction(deleteWorker, name, surname)

    if not worker:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        res = {'status': 'success'}
        return jsonify(res)
