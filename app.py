from flask import Flask, render_template, request, redirect, url_for, jsonify
import pymysql

app = Flask(__name__)

# MySQL Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Adithya@2005',
    'database': 'ci'
}

# Home Route - Citrix Dashboard
@app.route('/')
def citrix_home():
    return render_template('citrix_home.html')

# Customers Page
@app.route('/customers')
def customers():
    return render_template('customers.html')

# Foreman (Linux Inventory) Page
@app.route('/foreman')
def foreman():
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    # Fetch unique customer names for dropdown
    cursor.execute("SELECT DISTINCT Customer_Name FROM customers")
    customers = [row[0] for row in cursor.fetchall()]

    cursor.close()
    connection.close()

    return render_template('foreman.html', customers=customers)

# Fetch Customers Based on Category
@app.route('/customers/<category>', methods=['GET', 'POST'])
def customer_list(category):
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    if request.method == 'POST':
        # Get form data
        ops = request.form['OPS']
        team = request.form['Team']
        customer_name = request.form['Customer_Name']
        total_host_count = request.form['Total_Host_Count']
        citrix_mgmt_server = request.form['Citrix_MGMT_Server']
        total_vdis = request.form['Total_VDIs']

        # Insert into database
        insert_query = """
            INSERT INTO customers (OPS, Team, Customer_Name, Total_Host_Count, Citrix_MGMT_Server, Total_VDIs, Category) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (ops, team, customer_name, total_host_count, citrix_mgmt_server, total_vdis, category))
        connection.commit()

        return redirect(url_for('customer_list', category=category))

    # Fetch category-specific customers
    query = "SELECT OPS, Team, Customer_Name, Total_Host_Count, Citrix_MGMT_Server, Total_VDIs FROM customers WHERE Category = %s"
    cursor.execute(query, (category,))
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('customer_list.html', category=category, data=data)

# Fetch Unique Customer Names for Dropdown
@app.route('/get_customers')
def get_customers():
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    query = "SELECT DISTINCT Customer_Name FROM customers"
    cursor.execute(query)
    customers = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    connection.close()
    
    return jsonify({'customers': customers})

# Fetch Devices for Selected Customer in Foreman Page
@app.route('/get_devices/<customer_name>')
def get_devices(customer_name):
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    query = "SELECT id, ip_address, hostname, ssh_port, location, server_type, serial_no, make_model FROM devices WHERE customer_name = %s"
    cursor.execute(query, (customer_name,))
    devices = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({'devices': devices})

# Add New Device to Foreman Page
@app.route('/add_device', methods=['POST'])
def add_device():
    data = request.json

    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    insert_query = """
        INSERT INTO devices (customer_name, ip_address, hostname, ssh_port, location, server_type, serial_no, make_model)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        data['customer_name'],
        data['ip_address'],
        data['hostname'],
        data['ssh_port'],
        data['location'],
        data['server_type'],
        data['serial_no'],
        data['make_model']
    ))

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'status': 'success', 'message': 'Device added successfully'})

# Delete Device
@app.route('/delete_device/<int:device_id>', methods=['POST'])
def delete_device(device_id):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM devices WHERE id = %s", (device_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Device deleted successfully'})

# Route to edit device - Load Edit Page
@app.route('/edit_device/<int:device_id>', methods=['GET'])
def edit_device(device_id):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, customer_name, ip_address, hostname, ssh_port, location, server_type, serial_no, make_model 
        FROM devices 
        WHERE id = %s
    """, (device_id,))
    
    device = cursor.fetchone()
    cursor.close()
    conn.close()

    if not device:
        return "Device not found", 404

    device_data = {
        "id": device[0],
        "customer_name": device[1],
        "ip_address": device[2],
        "hostname": device[3],
        "ssh_port": device[4],
        "location": device[5],
        "server_type": device[6],
        "serial_no": device[7],
        "make_model": device[8]
    }

    return render_template('edit_device.html', device=device_data)
# Route to update the device details
@app.route('/update_device/<int:device_id>', methods=['POST'])
def update_device(device_id):
    # Fetch data from the form (not JSON)
    customer_name = request.form['customer_name']
    ip_address = request.form['ip_address']
    hostname = request.form['hostname']
    ssh_port = request.form['ssh_port']
    location = request.form['location']
    server_type = request.form['server_type']
    serial_no = request.form['serial_no']
    make_model = request.form['make_model']

    # Connect to MySQL
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    # Update query
    query = """
        UPDATE devices 
        SET customer_name=%s, ip_address=%s, hostname=%s, ssh_port=%s, 
            location=%s, server_type=%s, serial_no=%s, make_model=%s 
        WHERE id=%s
    """
    values = (customer_name, ip_address, hostname, ssh_port, location, server_type, serial_no, make_model, device_id)

    cursor.execute(query, values)
    conn.commit()
    
    # Close connection
    cursor.close()
    conn.close()
    
    # Redirect to Foreman page after update
    return redirect(url_for('foreman'))

# Total Inventory Page
@app.route('/total_inventory')
def total_inventory():
    return render_template('total_inventory.html')

# Fetch Total Inventory Data
@app.route('/get_total_inventory')
def get_total_inventory():
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    query = "SELECT * FROM total_inventory"
    cursor.execute(query)
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(data)

# Add Inventory Record
@app.route('/add_total_inventory', methods=['POST'])
def add_total_inventory():
    data = request.form
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    query = """INSERT INTO total_inventory 
    (OPS, Team, Customer_Name, Total_Host_Count, Citrix_MGMT_Server, Total_VDIs, 
    Total_Managed, VDI_Patch_Completed, Host_Patch_Completed, MGMT_Server_Patch, 
    Total_Patch_Completed, Pending_MGMT, Pending_VDI, Patch_Pending_Host, 
    Total_Pending, Q3_Status, Patching) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    cursor.execute(query, tuple(data.values()))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    return jsonify({"message": "Inventory added successfully"}), 200



# Route to load edit page with pre-filled data
@app.route('/edit_total_inventory/<int:id>', methods=['GET'])
def edit_total_inventory(id):
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    query = "SELECT * FROM total_inventory WHERE id = %s"
    cursor.execute(query, (id,))
    inventory = cursor.fetchone()

    cursor.close()
    connection.close()

    if not inventory:
        return "Record not found", 404

    return render_template('edit_total_inventory.html', inventory=inventory)

# Route to update the total inventory details
@app.route('/update_total_inventory/<int:id>', methods=['POST'])
def update_total_inventory(id):
    data = request.form

    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()

    update_query = """
        UPDATE total_inventory SET OPS=%s, Team=%s, Customer_Name=%s, 
        Total_Host_Count=%s, Citrix_MGMT_Server=%s, Total_VDIs=%s, 
        Total_Managed=%s, VDI_Patch_Completed=%s, Host_Patch_Completed=%s, 
        MGMT_Server_Patch=%s, Total_Patch_Completed=%s, Pending_MGMT=%s, 
        Pending_VDI=%s, Patch_Pending_Host=%s, Total_Pending=%s, Q3_Status=%s, 
        Patching=%s WHERE id=%s
    """
    
    cursor.execute(update_query, tuple(data.values()) + (id,))
    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for('total_inventory'))

if __name__ == '__main__':
    app.run(debug=True)
