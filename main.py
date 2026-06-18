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
    "soledad_fernandez": {"nombre": "Soledad Fernández Abreu", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "asuncion_olivares": {"nombre": "Asunción Olivares Peña", "empresa": "PROICAFOR", "tipo_acceso": "oficina"},
    "jose_sanchez": {"nombre": "José Sánchez", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "maria_eugenia_lopez": {"nombre": "Mª Eugenia López Baez", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "begona_bonis": {"nombre": "Begoña de Bonis", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "movil"},
    "sonia_gomez": {"nombre": "Sonia Esther Gómez Díaz", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "andres_caceres": {"nombre": "Andrés del Rosario Lorenzo Cáceres Mascareño", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "arsenio_cabrera": {"nombre": "Arsenio Ángel Cabrera", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "maria_moure": {"nombre": "María Nieves Moure Naveiro", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "francisco_padilla": {"nombre": "Francisco Javier Padilla González", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "santiago_gutierrez": {"nombre": "Santiago Gutiérrez Fariña", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"}
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
    "maria_moure": "1118",
    "francisco_padilla": "1839",
    "santiago_gutierrez": "5535"
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
        SELECT id, empleado_id, fecha, hora_entrada, hora_salida, tipo, empresa, ip, hora_pausa_inicio, hora_pausa_fin
        FROM fichajes
        ORDER BY fecha DESC, hora_entrada DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    resultado = []

    for fila in datos:
        emp_id = fila[1]

        empleado_data = EMPLEADOS.get(emp_id)
        
        if empleado_data:
            nombre = empleado_data.get("nombre", emp_id)
            empresa = empleado_data.get("empresa", "Sin empresa")
        else:
            nombre = emp_id
            empresa = "Sin empresa"
        
        resultado.append({
            "id": fila[0],
            "empleado": emp_id,
            "nombre": nombre,
            "empresa": empresa,
            "fecha": fila[2],
            "entrada": fila[3],
            "salida": fila[4],
            "tipo": fila[5],
            "ip": fila[7] if len(fila) > 7 else "-",
            "pausa_inicio": fila[8] if len(fila) > 8 else None,
            "pausa_fin": fila[9] if len(fila) > 9 else None
        })

    return {"fichajes": resultado}
    
@app.get("/estado")
def estado(empleado_id: str):

    conn = database.conectar()
    cursor = conn.cursor()

    hoy = datetime.now(ZoneInfo("Atlantic/Canary")).strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT hora_entrada, hora_salida FROM fichajes WHERE empleado_id=? AND fecha=?",
        (empleado_id, hoy)
    )

    registro = cursor.fetchone()
    conn.close()

    if registro is None:
        return {"estado": "sin_fichar"}

    entrada, salida = registro

    if entrada and not salida:
        return {"estado": "entrada_hecha"}

    if entrada and salida:
        return {"estado": "completo"}

    return {"estado": "sin_fichar"}   

# ✅ EXPORTAR EXCEL (ARREGLADO)
@app.get("/exportar_excel")
def exportar_excel(fecha_inicio: str = None, fecha_fin: str = None, empleado_id: str = None, empresa: str = None):

    conn = database.conectar()
    cursor = conn.cursor()

    query = "SELECT empleado_id,fecha,hora_entrada,hora_salida,tipo,empresa,hora_pausa_inicio,hora_pausa_fin FROM fichajes WHERE 1=1"
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

    ws.append(["Empleado","Empresa","Fecha","Entrada","Salida","Pausa no computable","Horas","Tipo"])
    
    total_minutos = 0

    for fila in datos:
        empleado, fecha, entrada, salida, tipo, empresa = fila

        horas = "-"
        if entrada and salida:
            h1 = datetime.strptime(entrada,"%H:%M:%S")
            h2 = datetime.strptime(salida,"%H:%M:%S")
            diff = h2 - h1

            minutos_totales = diff.seconds // 60

        # 🔹 DESCONTAR PAUSA SI EXISTE
            if fila[8] and fila[9]:  # pausa_inicio y pausa_fin
                p1 = datetime.strptime(fila[8], "%H:%M:%S")
                p2 = datetime.strptime(fila[9], "%H:%M:%S")
                pausa = p2 - p1
                minutos_totales -= pausa.seconds // 60

            horas = f"{minutos_totales//60}h {minutos_totales%60}m"
            total_minutos += minutos_totales

        nombre = EMPLEADOS.get(empleado,{}).get("nombre",empleado)
        
        # 🔹 calcular pausa para Excel
        pausa_texto = "-"
        
        if fila[6] and fila[7]:
            p1 = datetime.strptime(fila[6], "%H:%M:%S")
            p2 = datetime.strptime(fila[7], "%H:%M:%S")
            minutos = (p2 - p1).seconds // 60
            pausa_texto = f"{minutos//60}h {minutos%60}m"
            
        ws.append([nombre,empresa,fecha,entrada,salida,pausa_texto,horas,tipo])
        
    horas_total = total_minutos // 60
    minutos_total = total_minutos % 60

    ws.append([])  # línea en blanco

    ws.append(["", "", "", "", "", "TOTAL", f"{horas_total}h {minutos_total}m", ""])

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
        
@app.get("/pausa")
def pausa(empleado_id: str):

    conn = database.conectar()
    cursor = conn.cursor()

    hoy = datetime.now(ZoneInfo("Atlantic/Canary")).strftime("%Y-%m-%d")
    hora_actual = datetime.now(ZoneInfo("Atlantic/Canary")).strftime("%H:%M:%S")

    cursor.execute(
        "SELECT hora_entrada, hora_pausa_inicio, hora_pausa_fin FROM fichajes WHERE empleado_id=? AND fecha=?",
        (empleado_id, hoy)
    )

    registro = cursor.fetchone()

    # ❌ NO HA FICHADO ENTRADA
    if not registro or not registro[0]:
        conn.close()
        return {"mensaje": "Primero debes fichar entrada", "hora": hora_actual}

    entrada, pausa_inicio, pausa_fin = registro

    # 🔹 INICIAR PAUSA
    if pausa_inicio is None:
        cursor.execute(
            "UPDATE fichajes SET hora_pausa_inicio=? WHERE empleado_id=? AND fecha=?",
            (hora_actual, empleado_id, hoy)
        )
        conn.commit()
        conn.close()
        return {"mensaje": "Pausa iniciada", "hora": hora_actual}

    # 🔹 FINALIZAR PAUSA
    if pausa_inicio and pausa_fin is None:
        cursor.execute(
            "UPDATE fichajes SET hora_pausa_fin=? WHERE empleado_id=? AND fecha=?",
            (hora_actual, empleado_id, hoy)
        )
        conn.commit()
        conn.close()
        return {"mensaje": "Pausa finalizada", "hora": hora_actual}

    # ❌ YA TIENE PAUSA COMPLETA
    conn.close()
    return {"mensaje": "Ya has registrado una pausa hoy", "hora": hora_actual}