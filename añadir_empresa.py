import sqlite3

conn = sqlite3.connect("fichajes.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE fichajes ADD COLUMN empresa TEXT")

conn.commit()
conn.close()

print("Columna empresa añadida correctamente")