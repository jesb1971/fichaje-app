import sqlite3

def conectar():
    conn = sqlite3.connect("fichajes.db")
    return conn

def crear_tabla():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fichajes (
    	id INTEGER PRIMARY KEY AUTOINCREMENT,
    	empleado_id TEXT NOT NULL,
    	fecha TEXT NOT NULL,
    	hora_entrada TEXT,
    	hora_salida TEXT,
   	 tipo TEXT,
    	ip TEXT,
    	empresa TEXT,
    	creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
    """)

    conn.commit()
    conn.close()