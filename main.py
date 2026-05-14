    return {"mensaje": mensaje, "hora": hora}


# ✅ ESTADO (FUERA DE /fichar)
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


# ✅ EXPORTAR EXCEL CON RANGO (FUERA DE /admin)
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

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fichajes"

    ws.append(["Empleado", "Fecha", "Entrada", "Salida", "Tipo", "Empresa"])

    for fila in datos:
        ws.append(fila)

    ruta = "/var/data/fichajes_export.xlsx"
    wb.save(ruta)

    return FileResponse(
        ruta,
        filename="fichajes.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )