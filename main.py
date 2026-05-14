from zoneinfo import ZoneInfo
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
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
USUARIO = "admin"
PASSWORD = "1234"
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

@app.get("/hora")
def hora():
    return {"hora_servidor": datetime.now()}

@app.get("/login_page")
def login_page():
    return FileResponse("templates/login.html")

@app.get("/login")
def login(usuario: str, password: str):
    if usuario == USUARIO and password == PASSWORD:
        return {"ok": True, "token": TOKEN}
    return {"ok": False}

@app.get("/app", response_class=HTMLResponse)
def app_web():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 🔥 FICHAR (ESTABLE)
@app.get("/fichar")
def fichar(request: Request, empleado_id: str, pin: str):

    x_forwarded_for = request.headers.get("x-forwarded-for")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host

    # 🔐 VALIDAR PIN
    if PINS.get(empleado_id) != pin:
        guardar_alerta(empleado_id, "PIN_INCORRECTO", "Intento de acceso con PIN incorrecto", ip)
        print(f"🚨 INTENTO FALLIDO: {empleado_id} desde IP {ip}")
        raise HTTPException(status_code=403, detail="PIN incorrecto")

    # 🔒 VALIDACIÓN IP (ORIGINAL)
    IPS_PERMITIDAS = ["92.185.36.146",
                      "90.75.200.225",
                      "92.185.42.206"]

    def ip_valida(ip):
        return any(ip.startswith(prefijo) for prefijo in IPS_PERMITIDAS)

    tipo_acceso = EMPLEADOS.get(empleado_id, {}).get("tipo_acceso", "oficina")

    if tipo_acceso == "oficina" and not ip_valida(ip):
        guardar_alerta(empleado_id, "FUERA_DE_SEDE", "Fichaje fuera de red autorizada", ip)
        print(f"⚠️ FICHAJE FUERA DE SEDE: {empleado_id}")
        tipo = "remoto"
    else:
        tipo = "presencial"

    # 🏢 EMPRESA
    empresa = EMPLEADOS.get(empleado_id, {}).get("empresa", "Sin empresa")

    conn = database.conectar()
    cursor = conn.cursor()

    ahora = datetime.now(ZoneInfo("Atlantic/Canary"))
    fecha = ahora.strftime("%Y-%m-%d")
    hora = ahora.strftime("%H:%M:%S")

    cursor.execute("""
    SELECT * FROM fichajes 
    WHERE empleado_id = ? AND fecha = ?
    """, (empleado_id, fecha))

    registro = cursor.fetchone()

    if registro is None:
        cursor.execute("""
        INSERT INTO fichajes (empleado_id, fecha, hora_entrada, tipo, ip, empresa)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (empleado_id, fecha, hora, tipo, ip, empresa))
        mensaje = "Entrada registrada"

    elif registro[4] is None:
        cursor.execute("""
        UPDATE fichajes 
        SET hora_salida = ?
        WHERE id = ?
        """, (hora, registro[0]))
        mensaje = "Salida registrada"

    else:
        guardar_alerta(empleado_id, "DOBLE_FICHAJE", "Intento de fichar más de 2 veces", ip)
        mensaje = "Ya has fichado entrada y salida hoy"

    conn.commit()
    conn.close()

    return {"mensaje": mensaje, "hora": hora}
    
    @app.get("/estado")
    def estado(empleado_id: str):
        conn = database.conectar()
        cursor = conn.cursor()

        hoy = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
        SELECT hora_entrada, hora_salida
        FROM fichajes
        WHERE empleado_id = ? AND fecha = ?
        """, (empleado_id, hoy))

        registro = cursor.fetchone()
        conn.close()

        if registro is None:
            return {"estado": "sin_fichar"}
        elif registro[1] is None:
            return {"estado": "entrada_hecha"}
        else:
            return {"estado": "completo"}
            
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
    
@app.get("/admin")
def panel_admin(token: str = None):
    if token != TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado")
    return FileResponse(os.path.join(BASE_DIR, "templates", "admin.html"))
    
    @app.get("/exportar_excel")
def exportar_excel(fecha_inicio: str = None, fecha_fin: str = None):

    conn = database.conectar()
    cursor = conn.cursor()

    query = """
        SELECT empleado_id, fecha, hora_entrada, hora_salida, tipo, empresa
        FROM fichajes
    """

    params = []

    if fecha_inicio and fecha_fin:
        query += " WHERE fecha BETWEEN ? AND ?"
        params = [fecha_inicio, fecha_fin]

    query += " ORDER BY fecha DESC, hora_entrada DESC"

    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()

    # Crear Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fichajes"

    # Cabecera
    ws.append(["Empleado", "Fecha", "Entrada", "Salida", "Tipo", "Empresa"])

    # Datos
    for fila in datos:
        ws.append(fila)

    ruta = "/var/data/fichajes_export.xlsx"
    wb.save(ruta)

    return FileResponse(
        ruta,
        filename="fichajes.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )