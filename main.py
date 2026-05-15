from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import database
import openpyxl
import os
import qrcode

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

app = FastAPI()

# 🔥 STATIC
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Crear tablas
database.crear_tabla()
database.crear_tabla_alertas()

# 🔐 CONFIG
USUARIO = "rrhh"
PASSWORD = "Icadepro2026!"
TOKEN = "seguro123"

# 🏢 EMPLEADOS
EMPLEADOS = {
    "carla_martin": {"nombre": "Carla Martín Cabrera", "empresa": "ICADEPRO", "tipo_acceso": "oficina"},
    "cristo_diaz": {"nombre": "Cristo Díaz Miranda", "empresa": "ICADEPRO", "tipo_acceso": "oficina"},
    "eduardo_rivero": {"nombre": "Eduardo Rivero Armas", "empresa": "ICADEPRO", "tipo_acceso": "oficina"},
    "luichy_jorge": {"nombre": "María Luisa Jorge Cabrera", "empresa": "ICADEPRO", "tipo_acceso": "movil"},
    "pilar_ganuza": {"nombre": "Pilar Ganuza Ardid", "empresa": "ICADEPRO", "tipo_acceso": "movil"},
    "laura_perez": {"nombre": "Laura Pérez Gómez", "empresa": "ICADEPRO", "tipo_acceso": "oficina"},

    "candelaria_rodriguez": {"nombre": "Candelaria Rodríguez Jimenez", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "javier_alfonso": {"nombre": "Javier Alfonso Lorenzo", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "marta_cano": {"nombre": "Marta Cano Oliva", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "natalia_diaz": {"nombre": "Natalia Díaz Felipe", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "nazaret_ramos": {"nombre": "Nazaret Ramos Bethencourt", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "soledad_fernandez": {"nombre": "Soledad Fernández", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},

    "asuncion_olivares": {"nombre": "Asunción Olivares Peña", "empresa": "PROICAFOR", "tipo_acceso": "oficina"},

    "jose_sanchez": {"nombre": "José Sánchez", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "maria_eugenia_lopez": {"nombre": "Mª Eugenia López Baez", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "begona_bonis": {"nombre": "Begoña de Bonis", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "movil"},
    "sonia_gomez": {"nombre": "Sonia Esther Gómez Díaz", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "andres_caceres": {"nombre": "Andrés del Rosario Lorenzo Cáceres Mascareño", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "arsenio_cabrera": {"nombre": "Arsenio Ángel Cabrera", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "maria_moure": {"nombre": "María Nieves Moure Naveiro", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
}

# 🔐 PINES
PINS = {
    "pilar_ganuza": "6857",
    "begona_bonis": "9654",
    "maria_eugenia_lopez": "8024",
    "luichy_jorge": "2985",
    "jose_sanchez": "3639",
    "javier_alfonso": "4100",
    "eduardo_rivero": "2096",
    "nazaret_ramos": "7639",
    "asuncion_olivares": "8691",
    "carla_martin": "1336",
    "cristo_diaz": "7245",
    "laura_perez": "2741",
    "marta_cano": "1124",
    "soledad_fernandez": "5315",
    "candelaria_rodriguez": "6041",
    "natalia_diaz": "1797",
    "sonia_gomez": "6805",
    "andres_caceres": "6771",
    "arsenio_cabrera": "4389",
    "maria_moure": "1118"
}

# 🔴 ALERTAS
def guardar_alerta(empleado_id, tipo_alerta, descripcion, ip):
    conn = database.conectar()
    cursor = conn.cursor()

    ahora = datetime.now(ZoneInfo("Atlantic/Canary"))

    cursor.execute("""
    INSERT INTO alertas (empleado_id, tipo_alerta, descripcion, ip, fecha, hora)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        empleado_id,
        tipo_alerta,
        descripcion,
        ip,
        ahora.strftime("%Y-%m-%d"),
        ahora.strftime("%H:%M:%S")
    ))

    conn.commit()
    conn.close()

# 🔹 LOGIN PAGE
@app.get("/login_page")
def login_page():
    return FileResponse("templates/login.html")

# 🔐 LOGIN POST
@app.post("/login")
async def login(request: Request):
    data = await request.json()

    usuario = data.get("usuario")
    password = data.get("password")

    if usuario == USUARIO and password == PASSWORD:
        return {"ok": True, "token": TOKEN}

    return JSONResponse(content={"ok": False}, status_code=401)

# 🔹 PANEL ADMIN
@app.get("/admin")
def panel_admin(token: str = None):
    if token != TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado")
    return FileResponse(os.path.join(BASE_DIR, "templates", "admin.html"))

# 🔹 VER FICHAJES
@app.get("/ver_fichajes")
def ver_fichajes():

    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, empleado_id, fecha, hora_entrada, hora_salida, tipo, empresa, ip
        FROM fichajes
        ORDER BY fecha DESC, hora_entrada DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    resultado = []

    for fila in datos:
        emp_id = fila[1]

        nombre = EMPLEADOS.get(emp_id, {}).get("nombre", emp_id)
        empresa = EMPLEADOS.get(emp_id, {}).get("empresa", "Sin empresa")

        resultado.append({
            "id": fila[0],
            "empleado": emp_id,
            "nombre": nombre,
            "empresa": empresa,
            "fecha": fila[2],
            "entrada": fila[3],
            "salida": fila[4],
            "tipo": fila[5],
            "ip": fila[7] if len(fila) > 7 else "-"
        })

    return {"fichajes": resultado}

# 📥 EXPORTAR EXCEL
@app.get("/exportar_excel")
def exportar_excel(fecha_inicio: str = None, fecha_fin: str = None, empleado_id: str = None):

    conn = database.conectar()
    cursor = conn.cursor()

    query = """
        SELECT empleado_id, fecha, hora_entrada, hora_salida, tipo, empresa
        FROM fichajes
        WHERE 1=1
    """

    params = []

    # 🔹 Filtro por fechas
    if fecha_inicio and fecha_fin:
        query += " AND fecha BETWEEN ? AND ?"
        params.extend([fecha_inicio, fecha_fin])

    # 🔹 Filtro por empleado
    if empleado_id:
        query += " AND empleado_id = ?"
        params.append(empleado_id)

    query += " ORDER BY fecha DESC, hora_entrada DESC"

    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fichajes"

    ws.append(["Empleado","Empresa","Fecha","Entrada","Salida","Horas","Tipo"])

    for fila in datos:
        empleado, fecha, entrada, salida, tipo, empresa = fila
        
        horas = ""
        if entrada and salida:
            h1 = datetime.strptime(entrada, "%H:%M:%S")
            h2 = datetime.strptime(salida, "%H:%M:%S")
            diff = h2 - h1
            horas = f"{diff.seconds//3600}h {(diff.seconds%3600)//60}m"

        nombre = EMPLEADOS.get(empleado, {}).get("nombre", empleado)
        ws.append([nombre, empresa, fecha, entrada, salida, horas, tipo])

    ruta = "/var/data/fichajes_export.xlsx"
    wb.save(ruta)

    return FileResponse(
        ruta,
        filename="fichajes.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# 📄 EXPORTAR PDF
@app.get("/exportar_pdf")
def exportar_pdf(fecha_inicio: str = None, fecha_fin: str = None, empleado_id: str = None, empresa: str = None):

    conn = database.conectar()
    cursor = conn.cursor()

    query = """
        SELECT empleado_id, fecha, hora_entrada, hora_salida, tipo, empresa
        FROM fichajes
        WHERE 1=1
    """

    params = []

    if fecha_inicio and fecha_fin:
        query += " AND fecha BETWEEN ? AND ?"
        params.extend([fecha_inicio, fecha_fin])

    if empleado_id:
        query += " AND empleado_id = ?"
        params.append(empleado_id)

    if empresa:
        query += " AND empresa = ?"
        params.append(empresa)

    query += " ORDER BY fecha DESC, hora_entrada DESC"

    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()

    ruta = "/var/data/fichajes.pdf"

    doc = SimpleDocTemplate(ruta, pagesize=letter)

    tabla_data = [["Empleado", "Fecha", "Entrada", "Salida", "Tipo", "Empresa"]]

    for fila in datos:
        tabla_data.append(list(fila))

    tabla = Table(tabla_data)

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))

    doc.build([tabla])

    return FileResponse(ruta, filename="fichajes.pdf", media_type="application/pdf")