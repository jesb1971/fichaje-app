from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import database
import openpyxl
import os
import qrcode

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

# 🔹 RUTAS
@app.get("/")
def inicio():
    return {"mensaje": "Sistema de fichaje activo"}

@app.get("/login_page")
def login_page():
    return FileResponse("templates/login.html")

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    if data.get("usuario") == USUARIO and data.get("password") == PASSWORD:
        return {"ok": True, "token": TOKEN}
    return JSONResponse(content={"ok": False}, status_code=401)

@app.get("/app", response_class=HTMLResponse)
def app_web():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 🔥 FICHAR (CLAVE)
@app.get("/fichar")
def fichar(request: Request, empleado_id: str, pin: str):

    ip = request.headers.get("x-forwarded-for", request.client.host)
    ip = ip.split(",")[0].strip()

    if PINS.get(empleado_id) != pin:
        guardar_alerta(empleado_id, "PIN_INCORRECTO", "Intento fallido", ip)
        raise HTTPException(status_code=403, detail="PIN incorrecto")

    IPS_PERMITIDAS = ["92.185.36.146","90.75.200.225","92.185.42.206"]

    def ip_valida(ip):
        return any(ip.startswith(p) for p in IPS_PERMITIDAS)

    tipo = "presencial" if ip_valida(ip) else "remoto"
    empresa = EMPLEADOS.get(empleado_id, {}).get("empresa", "")

    conn = database.conectar()
    cursor = conn.cursor()

    ahora = datetime.now(ZoneInfo("Atlantic/Canary"))
    fecha = ahora.strftime("%Y-%m-%d")
    hora = ahora.strftime("%H:%M:%S")

    cursor.execute("SELECT * FROM fichajes WHERE empleado_id=? AND fecha=?", (empleado_id, fecha))
    registro = cursor.fetchone()

    if registro is None:
        cursor.execute("INSERT INTO fichajes (empleado_id,fecha,hora_entrada,tipo,ip,empresa) VALUES (?,?,?,?,?,?)",
                       (empleado_id,fecha,hora,tipo,ip,empresa))
        mensaje = "Entrada registrada"
    elif registro[4] is None:
        cursor.execute("UPDATE fichajes SET hora_salida=? WHERE id=?", (hora, registro[0]))
        mensaje = "Salida registrada"
    else:
        mensaje = "Ya has fichado hoy"

    conn.commit()
    conn.close()

    return {"mensaje": mensaje, "hora": hora}

# 🔹 DATOS PARA PANEL ADMIN
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

# ✅ EXPORTAR EXCEL (ARREGLADO)
@app.get("/exportar_excel")
def exportar_excel(fecha_inicio: str = None, fecha_fin: str = None, empleado_id: str = None, empresa: str = None):

    conn = database.conectar()
    cursor = conn.cursor()

    query = "SELECT empleado_id,fecha,hora_entrada,hora_salida,tipo,empresa FROM fichajes WHERE 1=1"
    params = []

    # 🔹 Filtro por fechas
    if fecha_inicio and fecha_fin:
        query += " AND fecha BETWEEN ? AND ?"
        params.extend([fecha_inicio, fecha_fin])

    # 🔹 Filtro por empleado (IMPORTANTE: aquí no tocamos lógica rara)
    if empleado_id:
        query += " AND empleado_id = ?"
        params.append(empleado_id)

    # 🔹 Filtro por empresa
    if empresa:
        query += " AND empresa = ?"
        params.append(empresa)

    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active

    ws.append(["Empleado","Empresa","Fecha","Entrada","Salida","Horas","Tipo"])

    for fila in datos:
        empleado, fecha, entrada, salida, tipo, empresa = fila

        horas = ""
        if entrada and salida:
            h1 = datetime.strptime(entrada,"%H:%M:%S")
            h2 = datetime.strptime(salida,"%H:%M:%S")
            diff = h2-h1
            horas = f"{diff.seconds//3600}h {(diff.seconds%3600)//60}m"

        nombre = EMPLEADOS.get(empleado,{}).get("nombre",empleado)
        ws.append([nombre,empresa,fecha,entrada,salida,horas,tipo])

    ruta="/var/data/fichajes.xlsx"
    wb.save(ruta)

    return FileResponse(ruta,filename="fichajes.xlsx")
    
    # 🔐 PANEL ADMIN (LO QUE TE FALTA)
@app.get("/admin", response_class=HTMLResponse)
def panel_admin(token: str = None):
    if token != TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado")

    ruta = os.path.join(BASE_DIR, "templates", "admin.html")

    if not os.path.exists(ruta):
        return {"error": "No existe admin.html"}

    with open(ruta, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())