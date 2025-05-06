from neo4j import GraphDatabase

class Neo4jConector:
    """Clase para manejar conexiones con Neo4j."""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    def run_query(self, query, parameters=None):
        return self.execute_query(query, parameters)

    def ejecutar_consulta(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record for record in result]