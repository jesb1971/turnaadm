import sqlite3
from werkzeug.security import generate_password_hash

# Conexión
conn = sqlite3.connect('turnos.db')
cur = conn.cursor()

# Tabla de turnos
cur.execute('''
CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    empleado TEXT NOT NULL,
    centro TEXT NOT NULL,
    turno TEXT NOT NULL,
    hora_entrada TEXT NOT NULL,
    hora_salida TEXT NOT NULL,
    observaciones TEXT
)
''')

# Tabla de usuarios
cur.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario TEXT NOT NULL UNIQUE,
    contraseña_hash TEXT NOT NULL
)
''')

# Insertar usuarios iniciales
usuarios_iniciales = [
    ('admin', generate_password_hash('admin123')),
    ('coordinacion', generate_password_hash('oficina456'))
]

for usuario, hash in usuarios_iniciales:
    cur.execute('SELECT id FROM usuarios WHERE nombre_usuario = ?', (usuario,))
    if not cur.fetchone():
        cur.execute('INSERT INTO usuarios (nombre_usuario, contraseña_hash) VALUES (?, ?)', (usuario, hash))

# Guardar cambios
conn.commit()
conn.close()
print("Base de datos inicializada con éxito.")
