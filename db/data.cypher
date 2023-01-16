CREATE (Grzegorz:Employee {name:"Hubert", surname: "Kowalski", position:"UI/UX"})
CREATE (Matylda:Employee {name:"Karol", surname: "Wiśniewski", position:"Recruiter"})
CREATE (Mariusz:Employee {name:"Kamil", surname: "Lisowski", position:"Tester"})
CREATE (Marysia:Employee {name:"Piotr", surname: "Damrych", position:"Intern"})
CREATE (Szymon:Employee {name:"Szymon", surname: "Kalkowski", position:"Fullstack"})
CREATE (IT:Department {name:"IT"})
CREATE (HR:Department {name:"HR"})

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Hubert' AND b.name = 'IT'
CREATE (a)-[r:WORKS_IN]->(b)
RETURN type(r)

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Szymon' AND b.name = 'IT'
CREATE (a)-[r:WORKS_IN]->(b)<-[:MANAGES]-(a)
RETURN type(r)

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Kamil' AND b.name = 'IT'
CREATE (a)-[r:WORKS_IN]->(b)
RETURN type(r)

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Karol' AND b.name = 'HR'
CREATE (a)-[r:WORKS_IN]->(b)<-[:MANAGES]-(a)
RETURN type(r)

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Szymon' AND b.name = 'HR'
CREATE (a)-[r:WORKS_IN]->(b)
RETURN type(r)