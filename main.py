from flask import Flask, render_template, request, redirect, session, url_for, send_file
import sqlite3
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'turnaadm2025'

# ---------------------- AUTENTICACIÓN COORDINACIÓN ----------------------

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    mensaje = request.args.get('mensaje')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'coordinacion' and password == 'admin123':
            session['usuario'] = username
            return redirect('/panel_turnos')
        else:
            error = 'Credenciales incorrectas'
    return render_template('login.html', error=error, mensaje=mensaje)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login', mensaje='Sesión cerrada correctamente.'))

# ---------------------- PANEL DE COORDINACIÓN ----------------------

@app.route('/panel_turnos')
def panel_turnos():
    if 'usuario' not in session:
        return redirect('/login')

    mensaje = request.args.get('mensaje')

    conn = sqlite3.connect('turnos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM turnos ORDER BY fecha DESC")
    turnos = cursor.fetchall()
    conn.close()

    turnos_con_clase = []
    for turno in turnos:
        centro = turno["centro"].strip().upper()
        if "ALVAREZ" in centro:
            clase = "alvarez"
        elif "DUGGI" in centro:
            clase = "duggi"
        elif "INGENIEROS" in centro:
            clase = "ingenieros"
        else:
            clase = ""
        turno_dict = dict(turno)
        turno_dict["centro_css"] = clase
        turnos_con_clase.append(turno_dict)

    return render_template('panel_turnos.html', turnos=turnos_con_clase, mensaje=mensaje)

# ---------------------- FORMULARIO CREACIÓN DE TURNOS ----------------------

@app.route('/formulario_turnos')
def formulario_turnos():
    if 'usuario' not in session:
        return redirect('/login')
    return render_template('formulario_turnos.html')

@app.route('/crear_turnos', methods=['POST'])
def crear_turnos():
    datos = zip(
        request.form.getlist('fecha[]'),
        request.form.getlist('empleado_dni[]'),
        request.form.getlist('centro[]'),
        request.form.getlist('turno[]'),
        request.form.getlist('hora_entrada[]'),
        request.form.getlist('hora_salida[]'),
        request.form.getlist('observaciones[]')
    )

    conn = sqlite3.connect('turnos.db')
    cursor = conn.cursor()

    for fila in datos:
        fecha, empleado_dni, centro, turno, entrada, salida, obs = fila
        if '|' in empleado_dni:
            nombre, dni = empleado_dni.split('|')
        else:
            nombre, dni = empleado_dni, ''
        cursor.execute("""
            INSERT INTO turnos (fecha, empleado, centro, turno, hora_entrada, hora_salida, observaciones, dni)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha, nombre.strip(), centro, turno, entrada, salida, obs, dni.strip()))

    conn.commit()
    conn.close()
    return redirect(url_for('panel_turnos', mensaje='Turnos guardados correctamente.'))

# ---------------------- EDICIÓN DE TURNOS ----------------------

@app.route('/editar_turno/<int:id>', methods=['GET'])
def editar_turno(id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('turnos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM turnos WHERE id = ?", (id,))
    turno = cursor.fetchone()
    conn.close()

    if turno:
        return render_template('editar_turno.html', turno=turno)
    else:
        return "Turno no encontrado", 404

@app.route('/actualizar_turno/<int:id>', methods=['POST'])
def actualizar_turno(id):
    if 'usuario' not in session:
        return redirect('/login')

    fecha = request.form['fecha']
    empleado = request.form['empleado']
    centro = request.form['centro']
    turno = request.form['turno']
    hora_entrada = request.form['hora_entrada']
    hora_salida = request.form['hora_salida']
    observaciones = request.form['observaciones']
    dni = request.form['dni']

    conn = sqlite3.connect('turnos.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE turnos SET 
            fecha = ?, empleado = ?, centro = ?, turno = ?, 
            hora_entrada = ?, hora_salida = ?, observaciones = ?, dni = ?
        WHERE id = ?
    """, (fecha, empleado, centro, turno, hora_entrada, hora_salida, observaciones, dni, id))
    conn.commit()
    conn.close()
    return redirect(url_for('panel_turnos', mensaje='Turno actualizado correctamente.'))

# ---------------------- ELIMINACIÓN DE TURNOS ----------------------

@app.route('/eliminar_turno/<int:id>', methods=['GET'])
def eliminar_turno(id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('turnos.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM turnos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('panel_turnos', mensaje='Turno eliminado correctamente.'))

# ---------------------- AUTENTICACIÓN DE USUARIOS ----------------------

@app.route('/login_usuario', methods=['GET', 'POST'])
def login_usuario():
    if request.method == 'POST':
        dni = request.form['dni']
        conn = sqlite3.connect('turnos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT empleado FROM turnos WHERE dni = ?", (dni,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            session['dni'] = dni
            session['empleado'] = resultado[0]
            return redirect('/panel_usuario')
        else:
            error = "DNI no encontrado o sin turnos asignados."
            return render_template('login_usuario.html', error=error)
    return render_template('login_usuario.html')

@app.route('/logout_usuario')
def logout_usuario():
    session.pop('dni', None)
    session.pop('empleado', None)
    return redirect('/login_usuario')

# ---------------------- PANEL DEL USUARIO ----------------------

@app.route('/panel_usuario')
def panel_usuario():
    if 'dni' not in session:
        return redirect('/login_usuario')

    dni = session['dni']
    conn = sqlite3.connect('turnos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fecha, centro, turno, hora_entrada, hora_salida, observaciones 
        FROM turnos 
        WHERE dni = ? 
        ORDER BY fecha
    """, (dni,))
    turnos = cursor.fetchall()
    conn.close()
    return render_template('panel_usuario.html', empleado=session['empleado'], turnos=turnos)

# ---------------------- EXPORTAR TURNOS A EXCEL (USUARIO) ----------------------

@app.route('/exportar_turnos')
def exportar_turnos():
    if 'dni' not in session:
        return redirect('/login_usuario')

    dni = session['dni']
    empleado = session['empleado'].replace(' ', '_')
    conn = sqlite3.connect('turnos.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fecha, centro, turno, hora_entrada, hora_salida, observaciones
        FROM turnos WHERE dni = ? ORDER BY fecha
    """, (dni,))
    datos = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(datos, columns=['Fecha', 'Centro', 'Turno', 'Hora Entrada', 'Hora Salida', 'Observaciones'])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Turnos')

    output.seek(0)
    filename = f"turnos_{empleado}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True)

# ---------------------- PANEL DE INFORMES ----------------------

@app.route('/panel_informes', methods=['GET'])
def panel_informes():
    if 'usuario' not in session or session['usuario'] != 'coordinacion':
        return redirect('/login')

    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    centro_filtro = request.args.get('centro')
    mensaje = request.args.get('mensaje')

    conn = sqlite3.connect('turnos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT empleado, centro, turno, hora_entrada, hora_salida, fecha, observaciones 
        FROM turnos 
        WHERE 1=1
    """
    params = []

    if fecha_inicio:
        query += " AND fecha >= ?"
        params.append(fecha_inicio)

    if fecha_fin:
        query += " AND fecha <= ?"
        params.append(fecha_fin)

    if centro_filtro:
        query += " AND centro LIKE ?"
        params.append(f"%{centro_filtro}%")

    query += " ORDER BY fecha DESC"
    cursor.execute(query, params)
    turnos = cursor.fetchall()
    conn.close()

    return render_template('panel_informes.html', turnos=turnos, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, centro_filtro=centro_filtro, mensaje=mensaje)

@app.route('/exportar_excel')
def exportar_excel():
    if 'usuario' not in session or session['usuario'] != 'coordinacion':
        return redirect('/login')

    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    centro_filtro = request.args.get('centro')

    conn = sqlite3.connect('turnos.db')
    cursor = conn.cursor()

    query = """
        SELECT empleado, centro, turno, hora_entrada, hora_salida, fecha, observaciones 
        FROM turnos 
        WHERE 1=1
    """
    params = []

    if fecha_inicio:
        query += " AND fecha >= ?"
        params.append(fecha_inicio)

    if fecha_fin:
        query += " AND fecha <= ?"
        params.append(fecha_fin)

    if centro_filtro:
        query += " AND centro LIKE ?"
        params.append(f"%{centro_filtro}%")

    query += " ORDER BY fecha DESC"
    cursor.execute(query, params)
    datos = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(datos, columns=['Empleado', 'Centro', 'Turno', 'Hora Entrada', 'Hora Salida', 'Fecha', 'Observaciones'])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Turnos')

    output.seek(0)
    return send_file(output, download_name='turnos_filtrados.xlsx', as_attachment=True)

# ---------------------- INICIO ----------------------

if __name__ == '__main__':
    app.run(debug=True)
