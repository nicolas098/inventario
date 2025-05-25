from flask import Flask, request, jsonify, make_response, render_template
import sqlite3
import xml.etree.ElementTree as ET
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_NAME = 'inventario.db'

# --------------------- Inicializar Base de Datos ---------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cantidad INTEGER,
                    precio REAL,
                    proveedor TEXT,
                    categoria TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# --------------------- Ruta Principal con HTML ---------------------
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        nombre = request.form['nombre']
        cantidad = int(request.form['cantidad'])
        precio = float(request.form['precio'])
        proveedor = request.form['proveedor']
        categoria = request.form['categoria']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO productos (nombre, cantidad, precio, proveedor, categoria) VALUES (?, ?, ?, ?, ?)",
                  (nombre, cantidad, precio, proveedor, categoria))
        conn.commit()
        conn.close()

    # Mostrar productos existentes
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM productos")
    productos = c.fetchall()
    conn.close()

    return render_template("index.html", productos=productos)

# --------------------- API REST ---------------------
@app.route('/create', methods=['POST'])
def create_producto():
    data = request.get_json()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO productos (nombre, cantidad, precio, proveedor, categoria) VALUES (?, ?, ?, ?, ?)",
              (data['nombre'], data['cantidad'], data['precio'], data['proveedor'], data['categoria']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Producto creado correctamente'})

@app.route('/read', methods=['GET'])
def read_productos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM productos")
    rows = c.fetchall()
    conn.close()
    productos = [{'id': r[0], 'nombre': r[1], 'cantidad': r[2], 'precio': r[3], 'proveedor': r[4], 'categoria': r[5]} for r in rows]
    return jsonify(productos)

@app.route('/update/<int:id>', methods=['PUT'])
def update_producto(id):
    data = request.get_json()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE productos SET nombre=?, cantidad=?, precio=?, proveedor=?, categoria=? WHERE id=?",
              (data['nombre'], data['cantidad'], data['precio'], data['proveedor'], data['categoria'], id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Producto actualizado'})

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_producto(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM productos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Producto eliminado'})

# --------------------- XML y Reportes ---------------------
@app.route('/report/xml', methods=['GET'])
def report_xml():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM productos")
    rows = c.fetchall()
    conn.close()

    root = ET.Element("productos")

    for r in rows:
        prod = ET.SubElement(root, "producto")
        ET.SubElement(prod, "id").text = str(r[0])
        ET.SubElement(prod, "nombre").text = r[1]
        ET.SubElement(prod, "cantidad").text = str(r[2])
        ET.SubElement(prod, "precio").text = str(r[3])
        ET.SubElement(prod, "proveedor").text = r[4]
        ET.SubElement(prod, "categoria").text = r[5]

    xml_str = ET.tostring(root, encoding='utf-8')
    response = make_response(xml_str)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/report/summary', methods=['GET'])
def report_summary():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT cantidad, precio, categoria FROM productos")
    rows = c.fetchall()
    conn.close()

    total_valor = sum([r[0] * r[1] for r in rows])

    categorias = {}
    for r in rows:
        cat = r[2]
        categorias[cat] = categorias.get(cat, 0) + 1

    total_productos = len(rows)
    porcentajes = {k: f"{(v / total_productos) * 100:.2f}%" for k, v in categorias.items()}

    return jsonify({
        "valor_total_inventario": total_valor,
        "porcentaje_por_categoria": porcentajes
    })

# --------------------- Run ---------------------
import os
if __name__ == '__main__':
    port = int(os.environ.get('PORT',10000))
    app.run(host='0.0.0.0', port=port)



