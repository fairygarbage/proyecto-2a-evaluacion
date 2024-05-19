from flask import Flask, jsonify, request, redirect, url_for, render_template
import mysql.connector

app = Flask(__name__)

# Configuración de la conexión a MySQL
def connect_to_node1():
    return mysql.connector.connect(
        host="localhost",
        port='3301',
        user="root",
        password="pwd",
        database="Base de Datos Distribuida OE"
    )

def connect_to_node2():
    return mysql.connector.connect(
        host="localhost",
        port='3302', 
        user="root",
        password="pwd",
        database="Region B"
    )

# Función para establecer la conexión con la base de datos del nodo 3 (Región C y D)
def connect_to_node3():
    return mysql.connector.connect(
        host="localhost",
        port='3303', 
        user="root",
        password="pwd",
        database="Region C"
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/customers')
def new_page_customers():
    return render_template('customers.html')


@app.route('/order_items')
def order_items():
    return render_template('order_items.html')

@app.route('/orders')
def orders():
    return render_template('orders.html')

@app.route('/fetch_orders')
def fetch_orders():
    """Obtiene las órdenes de la base de datos en el nodo dos y las devuelve como JSON."""
    try:
        connection = connect_to_node2()
        cursor = connection.cursor(dictionary=True)
        order_id = request.args.get('order_id')
        if order_id:
            cursor.execute("SELECT * FROM orders WHERE ORDER_ID = %s", (order_id,))
        else:
            cursor.execute("SELECT * FROM orders")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        
        orders = []
        for row in rows:
            orders.append({
                "ORDER_ID": row['ORDER_MODE'],
                "ORDER_DATE": row['ORDER_DATE'],
                "ORDER_MODE": row['CUSTOMER_ID'],
                "CUSTOMER_ID": row['ORDER_ID'],
                "ORDER_STATUS": row['ORDER_STATUS'],
                "ORDER_TOTAL": row['ORDER_TOTAL'],
                "SALES_REP_ID": row['PROMOTION_ID'],
                "PROMOTION_ID": row['SALES_REP_ID']
            })
        return jsonify(orders)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/add_order', methods=['POST'])
def add_order():
    """Agrega una nueva orden a la base de datos en el nodo dos y un nuevo item en el nodo uno."""
    try:
        order_id = request.form['order_id']
        
        # Conexión al nodo 2 para la tabla orders
        connection_node2 = connect_to_node2()
        cursor_node2 = connection_node2.cursor()

        order_date = request.form['order_date']
        order_mode = request.form['order_mode']
        customer_id = request.form['customer_id']
        order_status = request.form['order_status']
        order_total = request.form['order_total']
        sales_rep_id = request.form['sales_rep_id']
        promotion_id = request.form['promotion_id']

        # Inserción en la tabla orders
        cursor_node2.execute(
            """
            INSERT INTO orders (ORDER_ID, ORDER_DATE, ORDER_MODE, CUSTOMER_ID, ORDER_STATUS, ORDER_TOTAL, SALES_REP_ID, PROMOTION_ID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (order_id, order_date, order_mode, customer_id, order_status, order_total, sales_rep_id, promotion_id)
        )

        # Conexión al nodo 1 para la tabla order_items
        connection_node1 = connect_to_node1()
        cursor_node1 = connection_node1.cursor()

        line_item_id = request.form['line_item_id']
        product_id = request.form['product_id']
        unit_price = request.form['unit_price']
        quantity = request.form['quantity']

        # Inserción en la tabla order_items
        cursor_node1.execute(
            """
            INSERT INTO order_items (ORDER_ID, LINE_ITEM_ID, PRODUCT_ID, UNIT_PRICE, QUANTITY)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (order_id, line_item_id, product_id, unit_price, quantity)
        )

        # Realizar commit en ambas bases de datos
        connection_node2.commit()
        connection_node1.commit()

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor_node2.close()
        connection_node2.close()
        cursor_node1.close()
        connection_node1.close()

@app.route('/fetch_order_items', methods=['GET'])
def fetch_order_items():
    try:
        connection = connect_to_node1()
        cursor = connection.cursor(dictionary=True)
        order_id = request.args.get('order_id')
        if order_id:
            cursor.execute("SELECT * FROM ORDER_ITEMS WHERE ORDER_ID = %s", (order_id,))
        else:
            cursor.execute("SELECT * FROM ORDER_ITEMS")
        rows = cursor.fetchall()

        order_items = []
        for row in rows:
            order_items.append({
                "ORDER_ID": row["LINE_ITEM_ID"],
                "LINE_ITEM_ID": row["ORDER_ID"],
                "PRODUCT_ID": row["PRODUCT_ID"],
                "UNIT_PRICE": row["QUANTITY"],
                "QUANTITY": row["UNIT_PRICE"]
            })
        return jsonify(order_items)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        connection.close()

@app.route('/product_information')
def product_information():
    return render_template('product_information.html')

@app.route('/fetch_product_info', methods=['GET'])
def fetch_product_info():
    try:
        product_id = request.args.get('product_id')
        connection = connect_to_node3()  # Suponiendo que node3 es donde se encuentra la tabla PRODUCT_INFORMATION
        cursor = connection.cursor(dictionary=True)

        if product_id:
            cursor.execute("SELECT * FROM PRODUCT_INFORMATION WHERE PRODUCT_ID = %s", (product_id,))
        else:
            cursor.execute("SELECT * FROM PRODUCT_INFORMATION")
        
        rows = cursor.fetchall()
        product_info = []
        for row in rows:
            product_info.append({
                "PRODUCT_ID": row["WARRANTY_PERIOD"],
                "PRODUCT_NAME": row["SUPPLIER_ID"],
                "PRODUCT_DESCRIPTION": row["WEIGHT_CLASS"],
                "CATEGORY_ID": row["PRODUCT_NAME"],
                "WEIGHT_CLASS": row["CATALOG_URL"],
                "WARRANTY_PERIOD": row["MIN_PRICE"],
                "SUPPLIER_ID": row["LIST_PRICE"],
                "PRODUCT_STATUS": row["PRODUCT_STATUS"],
                "LIST_PRICE": row["PRODUCT_DESCRIPTION"],
                "MIN_PRICE": row["CATEGORY_ID"],
                "CATALOG_URL": row["PRODUCT_ID"]
            })
        return jsonify(product_info)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        connection.close()

@app.route('/add_product', methods=['POST'])
def add_product():
    """Agrega un nuevo producto a la base de datos."""
    try:
        connection = connect_to_node3() 
        cursor = connection.cursor()

        # Obtener los datos del formulario
        productId = request.form['productId']
        productName = request.form['productName']
        productDescription = request.form['productDescription']
        categoryId = request.form['categoryId']
        weightClass = request.form['weightClass']
        warrantyPeriod = request.form['warrantyPeriod']
        supplierId = request.form['supplierId']
        productStatus = request.form['productStatus']
        listPrice = request.form['listPrice']
        minPrice = request.form['minPrice']
        catalogUrl = request.form['catalogUrl']

        # Insertar los datos del nuevo producto en la tabla PRODUCT_INFORMATION
        cursor.execute("""
            INSERT INTO PRODUCT_INFORMATION (PRODUCT_ID, PRODUCT_NAME, PRODUCT_DESCRIPTION, CATEGORY_ID, WEIGHT_CLASS, WARRANTY_PERIOD, SUPPLIER_ID, PRODUCT_STATUS, LIST_PRICE, MIN_PRICE, CATALOG_URL)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (productId, productName, productDescription, categoryId, weightClass, warrantyPeriod, supplierId, productStatus, listPrice, minPrice, catalogUrl))

        connection.commit()  # Confirmar la transacción
        return "Agregado Exitosamente"
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        connection.close()

@app.route('/delete_product', methods=['POST'])
def delete_product():
    """Elimina un producto de la base de datos."""
    try:
        connection = connect_to_node3()  
        cursor = connection.cursor()

        productId = request.form['deleteProductId']

        cursor.execute("DELETE FROM PRODUCT_INFORMATION WHERE PRODUCT_ID = %s", (productId,))
        connection.commit()
        return "Borrado Exitosamente"
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        connection.close()


@app.route('/agregar_cliente', methods=['POST'])
def agregar_cliente():
    # Obtener los datos del formulario
    customer_id = request.form['customerId']
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    credit_limit = request.form['creditLimit']
    email = request.form['email']
    income_level = request.form['incomeLevel']
    region = request.form['region']

    # Determinar a qué nodo conectarse según la región
    if region == 'A':
        connection = connect_to_node1()
        table_name = 'CUSTOMERS_REGION_A'
    elif region == 'B':
        connection = connect_to_node2()
        table_name = 'CUSTOMERS_REGION_B'
    elif region in ['C', 'D']:
        connection = connect_to_node3()
        table_name = f'CUSTOMERS_REGION_C'
    else:
        return "Región inválida. Por favor, ingrese una región válida."


    cursor = connection.cursor()
    cursor.execute(f"SELECT CUSTOMER_ID FROM {table_name} WHERE CUSTOMER_ID = %s", (customer_id,))
    existing_customer = cursor.fetchone()

    if existing_customer:
        connection.close()
        return "El CUSTOMER_ID ya existe en la base de datos. Por favor, ingresa un CUSTOMER_ID diferente."
    else:
        # Si el CUSTOMER_ID no existe, agregar el nuevo cliente a la base de datos
        query = f"""
            INSERT INTO {table_name} (CUSTOMER_ID, CUST_FIRST_NAME, CUST_LAST_NAME, CREDIT_LIMIT, CUST_EMAIL, INCOME_LEVEL, REGION)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (customer_id, first_name, last_name, credit_limit, email, income_level, region))

        # Realizar commit después de la inserción
        connection.commit()
        connection.close()
        return redirect(url_for('agregar_cliente'))

@app.route('/agregar_cliente')
def agregar_cliente_exito():
    return "Nuevo cliente agregado exitosamente."

# Ruta para actualizar un cliente
@app.route('/actualizar_cliente', methods=['POST'])
def actualizar_cliente():
    customer_id = request.form['customerId']
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    credit_limit = request.form['creditLimit']
    email = request.form['email']
    income_level = request.form['incomeLevel']
    region = request.form['region']

    if region == 'A':
        connection = connect_to_node1()
        table_name = 'CUSTOMERS_REGION_A'
    elif region == 'B':
        connection = connect_to_node2()
        table_name = 'CUSTOMERS_REGION_B'
    elif region in ['C', 'D']:
        connection = connect_to_node3()
        table_name = f'CUSTOMERS_REGION_C'
    else:
        return "Región inválida. Por favor, ingrese una región válida."

    cursor = connection.cursor()
    cursor.execute(f"SELECT CUSTOMER_ID FROM {table_name} WHERE CUSTOMER_ID = %s", (customer_id,))
    existing_customer = cursor.fetchone()
    
    if existing_customer:
        cursor = connection.cursor()
        query = f"""
            UPDATE {table_name}
            SET CUST_FIRST_NAME = %s, CUST_LAST_NAME = %s, CREDIT_LIMIT = %s, CUST_EMAIL = %s, INCOME_LEVEL = %s
            WHERE CUSTOMER_ID = %s
        """
        cursor.execute(query, (first_name, last_name, credit_limit, email, income_level, customer_id))
        connection.commit()
        connection.close()
        return redirect(url_for('actualizar_cliente_exito'))
    else:
        connection.close()
        return "El CUSTOMER_ID no existe en la base de datos"

@app.route('/actualizar_cliente_exito')
def actualizar_cliente_exito():
    return "Cliente actualizado exitosamente."

# Ruta para eliminar un cliente
@app.route('/eliminar_cliente', methods=['POST'])
def eliminar_cliente():
    customer_id = request.form['customerId']
    region = request.form['region']

    if region == 'A':
        connection = connect_to_node1()
        table_name = 'CUSTOMERS_REGION_A'
    elif region == 'B':
        connection = connect_to_node2()
        table_name = 'CUSTOMERS_REGION_B'
    elif region in ['C', 'D']:
        connection = connect_to_node3()
        table_name = f'CUSTOMERS_REGION_C'
    else:
        return "Región inválida. Por favor, ingrese una región válida."

    cursor = connection.cursor()
    cursor.execute(f"SELECT CUSTOMER_ID FROM {table_name} WHERE CUSTOMER_ID = %s", (customer_id,))
    existing_customer = cursor.fetchone()
    if existing_customer:
        query = f"DELETE FROM {table_name} WHERE CUSTOMER_ID = %s"
        cursor.execute(query, (customer_id,))
        connection.commit()
        connection.close()
        return redirect(url_for('eliminar_cliente_exito'))
    else:
        connection.close()
        return "El CUSTOMER_ID no existe en la base de datos"

@app.route('/eliminar_cliente_exito')
def eliminar_cliente_exito():
    return "Cliente eliminado exitosamente."


@app.route('/fetch_customers_region_a')
def fetch_customers():
    connection = connect_to_node1()
    if connection is None:
        return jsonify({"error": "Failed to connect to database"}), 500

    cursor = connection.cursor()
    query = "SELECT * FROM CUSTOMERS_REGION_A"
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()

    # Convertir los resultados a una lista de diccionarios
    customers = []
    for row in rows:
        customers.append({
            "CUSTOMER_ID": row[1],
            "CUST_FIRST_NAME": row[3],
            "CUST_LAST_NAME": row[4],
            "CREDIT_LIMIT": row[0],
            "CUST_EMAIL": row[2],
            "INCOME_LEVEL": row[5],
            "REGION": row[6]
        })

    return jsonify(customers)

@app.route('/fetch_customers_region_b')
def fetch_customers_region_b():
    connection = connect_to_node2()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM CUSTOMERS_REGION_B")
    customers = cursor.fetchall()
    connection.close()
    return jsonify(customers)

@app.route('/fetch_customers_region_c')
def fetch_customers_region_c():
    connection = connect_to_node3()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM CUSTOMERS_REGION_C WHERE REGION = 'C'")
    customers = cursor.fetchall()
    connection.close()
    return jsonify(customers)

@app.route('/fetch_customers_region_d')
def fetch_customers_region_d():
    connection = connect_to_node3()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM CUSTOMERS_REGION_C WHERE REGION = 'D'")
    customers = cursor.fetchall()
    connection.close()
    return jsonify(customers)

if __name__ == '__main__':
    app.run(debug=True)
