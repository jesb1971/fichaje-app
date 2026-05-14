import sqlite3

def conectar():
    conn = sqlite3.connect("/var/data/fichajes.db")
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

def crear_tabla_alertas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empleado_id TEXT,
        tipo_alerta TEXT,
        descripcion TEXT,
        ip TEXT,
        fecha TEXT,
        hora TEXT
    )
    """)

    conn.commit()
    conn.close()