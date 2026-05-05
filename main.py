from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import database
import openpyxl
import os
import qrcode

app = FastAPI()

from datetime import datetime, timedelta  # 👈 IMPORTANTE

INTENTOS_FALLIDOS = {}
BLOQUEOS = {}          # 👈 NUEVO
MAX_INTENTOS = 3
TIEMPO_BLOQUEO = 5     # 👈 NUEVO (minutos)

# 🔥 STATIC
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Crear tabla
database.crear_tabla()
database.crear_tabla_alertas()

# 🔐 LOGIN CONFIG
USUARIO = "admin"
PASSWORD = "1234"
TOKEN = "seguro123"

# 🏢 EMPLEADOS + EMPRESA
EMPLEADOS = {

    # 🟦 ICADEPRO
    "carla_martin": {"nombre": "Carla Martín Cabrera", "empresa": "ICADEPRO", "tipo_acceso": "oficina"},
    "cristo_diaz": {"nombre": "Cristo Díaz Miranda", "empresa": "ICADEPRO", "tipo_acceso": "oficina"},
    "eduardo_rivero": {"nombre": "Eduardo Rivero Armas", "empresa": "ICADEPRO", "tipo_acceso": "oficina"},
    "luichy_jorge": {"nombre": "María Luisa Jorge Cabrera", "empresa": "ICADEPRO", "tipo_acceso": "movil"},  # 👈 AUTORIZADA
    "pilar_ganuza": {"nombre": "Pilar Ganuza Ardid", "empresa": "ICADEPRO", "tipo_acceso": "movil"},        # 👈 AUTORIZADA
    "laura_perez": {"nombre": "Laura Pérez Gómez", "empresa": "ICADEPRO", "tipo_acceso": "oficina"},

    # 🟩 PROYECTOS EMPRESARIALES CANARIOS
    "candelaria_rodriguez": {"nombre": "Candelaria Rodríguez Jimenez", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "javier_alfonso": {"nombre": "Javier Alfonso Lorenzo", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "marta_cano": {"nombre": "Marta Cano Oliva", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "natalia_diaz": {"nombre": "Natalia Díaz Felipe", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "nazaret_ramos": {"nombre": "Nazaret Ramos Bethencourt", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},
    "soledad_fernandez": {"nombre": "Soledad Fernández", "empresa": "Proyectos Empresariales Canarios", "tipo_acceso": "oficina"},

    # 🟪 PROICAFOR
    "asuncion_olivares": {"nombre": "Asunción Olivares Peña", "empresa": "PROICAFOR", "tipo_acceso": "oficina"},

    # 🟨 AUTÓNOMOS (solo Begoña autorizada)
    "jose_sanchez": {"nombre": "José Sánchez", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "maria_eugenia_lopez": {"nombre": "Mª Eugenia López Baez", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "oficina"},
    "begona_bonis": {"nombre": "Begoña de Bonis", "empresa": "GRUPO ICADEPRO", "tipo_acceso": "movil"},  # 👈 AUTORIZADA
}

def guardar_alerta(empleado_id, tipo_alerta, descripcion, ip):
    conn = database.conectar()
    cursor = conn.cursor()

    ahora = datetime.now()
    fecha = ahora.strftime("%Y-%m-%d")
    hora = ahora.strftime("%H:%M:%S")

    cursor.execute("""
    INSERT INTO alertas (empleado_id, tipo_alerta, descripcion, ip, fecha, hora)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (empleado_id, tipo_alerta, descripcion, ip, fecha, hora))

    conn.commit()
    conn.close()

def intentos_recientes(empleado_id, minutos=5):
    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) FROM alertas
    WHERE empleado_id = ?
    AND tipo_alerta = 'PIN_INCORRECTO'
    AND datetime(fecha || ' ' || hora) >= datetime('now', ?)
    """, (empleado_id, f'-{minutos} minutes'))

    total = cursor.fetchone()[0]
    conn.close()
    return total

# 🔐 PINES (SIN CAMBIOS)
PINS = {
    "pilar_ganuza": "7942",
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
    "candelaria_rodriguez": "5050",
    "natalia_diaz": "6060"
}

@app.get("/")
def inicio():
    return {"mensaje": "Sistema de fichaje activo"}

@app.get("/hora")
def hora():
    return {"hora_servidor": datetime.now()}

# 🔐 LOGIN
@app.get("/login_page")
def login_page():
    return FileResponse("templates/login.html")

@app.get("/login")
def login(usuario: str, password: str):
    if usuario == USUARIO and password == PASSWORD:
        return {"ok": True, "token": TOKEN}
    return {"ok": False}

# 👇 APP

@app.get("/app", response_class=HTMLResponse)
def app_web():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/fichar")
def fichar(request: Request, empleado_id: str, pin: str, tipo: str = "presencial"):

    ip = request.client.host

    # 🔐 VALIDAR PIN
    if PINS.get(empleado_id) != pin:

        guardar_alerta(
            empleado_id,
            "PIN_INCORRECTO",
            "Intento de acceso con PIN incorrecto",
            ip
        )

        raise HTTPException(
            status_code=403,
            detail="PIN incorrecto"
        )

    # 🔒 CONTROL DE ACCESO POR IP
    tipo_acceso = EMPLEADOS.get(empleado_id, {}).get("tipo_acceso", "oficina")

    IPS_PERMITIDAS = [
        "127.0.0.1",
        "192.168.0.",
        "192.168.1.",
    ]

    def ip_valida(ip):
        return any(ip.startswith(prefijo) for prefijo in IPS_PERMITIDAS)

    if tipo_acceso == "oficina" and not ip_valida(ip):
        guardar_alerta(empleado_id, "FUERA_DE_SEDE", "Fichaje fuera de red", ip)
        print(f"⚠️ FICHAJE FUERA DE SEDE: {empleado_id} desde IP {ip}")
        mensaje_extra = "⚠️ Has fichado fuera de una sede autorizada"
    else:
        mensaje_extra = ""

    # 🏢 DATOS EMPRESA
    datos_emp = EMPLEADOS.get(empleado_id, {})
    empresa = datos_emp.get("empresa", "Sin empresa")

    conn = database.conectar()
    cursor = conn.cursor()

    ahora = datetime.now()
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

    return {
        "mensaje": mensaje,
        "hora": hora,
        "aviso": mensaje_extra
    }

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
        empresa_final = EMPLEADOS.get(emp_id, {}).get("empresa", "Sin empresa")

        resultado.append({
           "id": fila[0],
           "empleado": emp_id,
           "nombre": nombre,
           "empresa": empresa_final,
           "fecha": fila[2],
           "entrada": fila[3],
           "salida": fila[4],
           "tipo": fila[5],
           "ip": fila[6] if len(fila) > 6 else "-"
})

    return {"fichajes": resultado}
# 🔐 ADMIN
@app.get("/admin")
def panel_admin(token: str = None):
    if token != TOKEN:
        raise HTTPException(status_code=403, detail="No autorizado")
    return FileResponse("templates/admin.html")

# 📊 EXCEL
@app.get("/exportar_excel")
def exportar_excel():
    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT empleado_id, fecha, hora_entrada, hora_salida, tipo, empresa 
    FROM fichajes
    ORDER BY fecha DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fichajes"

    ws.append(["Empleado", "Empresa", "Fecha", "Entrada", "Salida", "Tipo"])

    for fila in datos:
        nombre = EMPLEADOS.get(fila[0], {}).get("nombre", fila[0])

        ws.append([
            nombre,
            fila[5],
            fila[1],
            fila[2],
            fila[3],
            fila[4]
        ])

    archivo = "fichajes.xlsx"
    wb.save(archivo)

    return FileResponse(archivo, filename=archivo)

# 🔥 QR

@app.get("/qr", response_class=HTMLResponse)
def generar_qr():

    html = """
    <html>
    <head>
    <title>QR Empleados - IcadePro</title>
    <style>
    body { font-family: Arial; text-align: center; }
    .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
    .card { border: 1px solid #ddd; padding: 15px; border-radius: 10px; }
    img { width: 150px; }
    </style>
    </head>
    <body>
    <h1>QR Fichaje - IcadePro</h1>
    <div class="grid">
    """

    BASE_URL = "http://127.0.0.1:8000/app"

    for emp_id, datos in EMPLEADOS.items():
        url = f"{BASE_URL}?empleado_id={emp_id}"

        img = qrcode.make(url)
        filename = f"static/qr_{emp_id}.png"
        img.save(filename)

        html += f"""
        <div class="card">
            <h3>{datos['nombre']}</h3>
            <p>{datos['empresa']}</p>
            <img src="/static/qr_{emp_id}.png">
        </div>
        """

    html += "</div></body></html>"

    return html

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from fastapi.responses import FileResponse

@app.get("/exportar_pdf")
def exportar_pdf():

    conn = database.conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT empleado_id, empresa, fecha, hora_entrada, hora_salida
    FROM fichajes
    ORDER BY empleado_id, fecha
    """)

    datos = cursor.fetchall()
    conn.close()

    archivo = "fichajes.pdf"
    doc = SimpleDocTemplate(archivo, pagesize=letter)

    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("REGISTRO DE HORARIOS", styles["Title"]))
    elementos.append(Paragraph("Control horario conforme a normativa", styles["Normal"]))

    # Agrupar por empleado
    empleados = {}

    for emp_id, empresa, fecha, entrada, salida in datos:
        nombre = EMPLEADOS.get(emp_id, {}).get("nombre", emp_id)
        empresa_final = EMPLEADOS.get(emp_id, {}).get("empresa", "No registrada")

        if nombre not in empleados:
            empleados[nombre] = {
                "empresa": empresa_final,
                "registros": []
            }

        empleados[nombre]["registros"].append([fecha, entrada or "-", salida or "-"])

    from datetime import datetime

    for nombre, info in empleados.items():

        elementos.append(Paragraph(f"<br/><b>Empleado:</b> {nombre}", styles["Normal"]))
        elementos.append(Paragraph(f"<b>Empresa:</b> {info['empresa']}", styles["Normal"]))

        tabla_data = [["Fecha", "Entrada", "Salida", "Horas"]]

        for fila in info["registros"]:
            fecha, entrada, salida = fila

            horas = "-"
            if entrada != "-" and salida != "-":
                t1 = datetime.strptime(entrada, "%H:%M:%S")
                t2 = datetime.strptime(salida, "%H:%M:%S")
                diff = t2 - t1
                horas = str(diff)

            tabla_data.append([fecha, entrada, salida, horas])

        tabla = Table(tabla_data)

        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
        ]))

        elementos.append(tabla)

    doc.build(elementos)

    return FileResponse(archivo, filename=archivo)