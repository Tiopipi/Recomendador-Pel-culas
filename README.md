# Motor de Recomendación de Películas (MRP)

Este proyecto implementa un sistema de recomendación de películas utilizando bases de datos no relacionales, análisis de grafos y un modelo de lenguaje (LLM) para mejorar la interacción con el usuario.

---

## Requisitos

Antes de ejecutar la aplicación, asegúrate de tener instaladas las siguientes herramientas:

- [Ollama](https://ollama.com/)
- [Neo4j Desktop](https://neo4j.com/download/)
- [MongoDB Community Server](https://www.mongodb.com/try/download/community)
- [MongoDB Compass](https://www.mongodb.com/products/compass)

---

## Pasos para la instalación y ejecución

### 1. Descargar el modelo LLM

Este sistema utiliza un modelo de lenguaje para generar respuestas personalizadas. Para descargarlo, ejecuta el siguiente comando en la terminal:

```bash
ollama pull gemma3:4b
```
Esto descargará el modelo gemma3 (versión 4b) necesario para las recomendaciones.

### 2. Importar la base de datos para MongoDB Compass
- Abre MongoDB Compass
- Crea una nueva conexión llamada BDNR y conéctate
- Crea la base de datos MRP y la colección 'peliculas'
- Haz clic en “Import Data” y selecciona el fichero el MRP.peliculas.json que se encuentra en la carpeta bases_de_datos del proyecto
### 3. Importar la base de datos en Neo4j desktop
- Abre Neo4j Desktop y crea un proyecto ‘Film Recommender’
- Añade el dump: Add > File > neo4j.dump (El fichero es el que se encuentra en el sharepoint)
- Crea una nueva BD desde el dump:
    - Nombre: neo4j
    - Contraseña: Virt1234*
- Inicia la base de datos
### 4. Instalar dependencias y ejecutar la aplicación
- Crear un entorno virtual para el proyecto (opcional)
- Instalar las dependencias
```bash
pip install -r requirements.txt
```
- Ejecutar la aplicación desde la raíz del proyecto
```bash
streamlit run app/app.py
```


