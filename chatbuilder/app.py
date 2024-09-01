from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import sqlite3

app = FastAPI()

# Montar archivos estáticos desde el directorio "static"
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# Crear la base de datos y las tablas si no existen
def initialize_database():
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()

    # Crear tabla de proyectos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    )
    """)

    # Crear tabla de nodos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        node_id TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        posX INTEGER NOT NULL,
        posY INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)

    # Crear tabla de conexiones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_node TEXT NOT NULL,
        target_node TEXT NOT NULL,
        label TEXT,
        project_id INTEGER NOT NULL,
        FOREIGN KEY (source_node) REFERENCES nodes(node_id),
        FOREIGN KEY (target_node) REFERENCES nodes(node_id),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )
    """)

    conn.commit()
    conn.close()

# Llamar a la función para inicializar la base de datos
initialize_database()

# Ruta para obtener el HTML de la aplicación
@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("templates/index.html") as f:
        return HTMLResponse(content=f.read())

# Ruta para obtener los proyectos disponibles
@app.get("/get_projects/")
async def get_projects():
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM projects")
    projects = cursor.fetchall()
    conn.close()
    return {"projects": projects}

# Ruta para obtener los datos de un proyecto específico (nodos y conexiones)
@app.get("/get_project_data/{project_id}/")
async def get_project_data(project_id: int):
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()

    # Obtener nodos del proyecto
    cursor.execute("SELECT node_id, label, posX, posY FROM nodes WHERE project_id = ?", (project_id,))
    nodes = cursor.fetchall()

    # Obtener conexiones del proyecto
    cursor.execute("SELECT source_node, target_node, label FROM connections WHERE project_id = ?", (project_id,))
    connections = cursor.fetchall()

    conn.close()

    if not nodes and not connections:
        raise HTTPException(status_code=404, detail="Project not found")

    # Formatear nodos y conexiones para el frontend
    node_list = [{"node_id": node[0], "label": node[1], "posX": node[2], "posY": node[3]} for node in nodes]
    connection_list = [{"source_node": connection[0], "target_node": connection[1], "label": connection[2]} for connection in connections]

    return {"nodes": node_list, "connections": connection_list}

# Ruta para guardar un nodo
@app.post("/save_node/")
async def save_node(data: dict):
    if "label" not in data:
        raise HTTPException(status_code=400, detail="label is required")

    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO nodes (node_id, label, posX, posY, project_id) VALUES (?, ?, ?, ?, ?)",
        (data["node_id"], data["label"], data["posX"], data["posY"], data["project_id"])
    )
    conn.commit()
    conn.close()
    return {"status": "Node saved successfully"}

# Ruta para actualizar un nodo
@app.put("/update_node/")
async def update_node(data: dict):
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE nodes SET label = ?, posX = ?, posY = ? WHERE node_id = ?",
        (data["label"], data["posX"], data["posY"], data["node_id"])
    )
    conn.commit()
    conn.close()
    return {"status": "Node updated successfully"}

# Ruta para guardar una conexión
@app.post("/save_connection/")
async def save_connection(data: dict):
    project_id = data.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")

    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO connections (source_node, target_node, label, project_id) VALUES (?, ?, ?, ?)",
        (data["source_node"], data["target_node"], data["label"], project_id)
    )
    conn.commit()
    conn.close()
    return {"status": "Connection saved successfully"}

# Ruta para guardar un proyecto
@app.post("/save_project/")
async def save_project(data: dict):
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (name, description) VALUES (?, ?)",
        (data["name"], data["description"])
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"project_id": project_id, "status": "Project saved successfully"}

# Ruta para actualizar un proyecto
@app.put("/update_project/")
async def update_project(data: dict):
    conn = sqlite3.connect("workflow.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE projects SET name = ?, description = ? WHERE id = ?",
        (data["name"], data["description"], data["project_id"])
    )
    conn.commit()
    conn.close()
    return {"status": "Project updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
