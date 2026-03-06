from mysql.connector import Error
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, get_jwt, jwt_required, get_jwt_identity



app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key_here'  # TODO: Ändra detta till en slumpmässig hemlig nyckel
jwt = JWTManager(app)

# Databaskonfiguration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Ändra detta till ditt MySQL-användarnamn
    'password': '',  # Ändra detta till ditt MySQL-lösenord
    'database': 'inlamning_1'
}
# hel
def get_db_connection():
    """Skapa och returnera en databasanslutning"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Fel vid anslutning till MySQL: {e}")
        return None


@app.route('/', methods=['GET'])
def index():
    return '''<h1>Documentation</h1>
    <ul><li>GET /users</li></ul>
    <ul><li>To create user: /users {“username”:”test”, “name”: “test”, "age":"99"}</li></ul>'''

# @app.route('/users', methods=['GET'])
# def get_users():
#     users = [
#         {"color": "Red", "id": 1, "fruit": "Grenade Apple"},
#         {"color": "Yellow", "id": 2, "fruit": "Banana"},
#         {"color": "Green", "id": 3, "fruit": "Melon"}
#     ]
#     return jsonify(users)

# @app.route('/users', methods=['GET'])
# def get_users():
#     """Get all users"""
#     users = get_db_connection()
#     return jsonify(users)

# @app.route('/users', methods=['GET'])
# def get_users():
#     users = [
#         {"color": "Red", "id": 1, "fruit": "Grenade Apple"},
#         {"color": "Yellow", "id": 2, "fruit": "Banana"},
#         {"color": "Green", "id": 3, "fruit": "Melon"}
#     ]
#     """Get all users"""
#     username = request.args.get('username', '')
#     print(username)


@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    sql = "SELECT username, name, email, age FROM users"
    cursor.execute(sql)
    users = cursor.fetchall()
   
    return jsonify(users)


@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get all users"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # hämta ENDAST user med id
    sql = "SELECT * FROM users WHERE id = %s"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()
   
    user.pop('password')
    if not user: # saknades personen i databasen?
        return jsonify({'error': 'User not found'}), 404
    else:
        return jsonify(user)
       

@app.route('/users/age/<int:user_age>', methods=['GET'])
@jwt_required()
def get_user_age(user_age):
    """Get all users"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # hämta ENDAST user med age
    sql = "SELECT * FROM users WHERE age = %s"
    cursor.execute(sql, (user_age,))
    user = cursor.fetchall()
   
    if not user: # saknades personen i databasen?
        return jsonify({'error': 'User not found'}), 404
    else:
        return jsonify(user)


@app.route('/create', methods=['POST'])
@jwt_required()
def create_user():
    """Create a new user"""
    data = request.get_json()  # Hämta data från requesten.
    username = data.get('username')
    name = data.get('name')
    age = data.get('age')
    password = data.get('password')
    email = data.get('email')
        
    connection = get_db_connection()
        
    cursor = connection.cursor()
    sql = "INSERT INTO users (username, name, age, password, email) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (username, name, age, generate_password_hash(password), email))
        
    connection.commit() # commit() gör klart skrivningen till databasen
    user_id = cursor.lastrowid # cursor.lastrowid innehåller id på raden som skapades i DB
        
    user = {
    'id': user_id,
    'username': username,
    'name': name,
    'age': age,
    'password': password,
    'email': email
    }
    return jsonify(user), 201 # HTTP Status 201 Created


# api-4
@app.route('/users/input', methods=['POST'])
@jwt_required()
def creating_user():
    data = request.get_json(silent=True)

    if is_valid_user_data(data):
        # Logik för databas här...

        data = request.get_json()  # Hämta data från requesten.
        username = data.get('username')
        name = data.get('name')
        age = data.get('age')
        password = data.get('password')
        email = data.get('email')
            
        connection = get_db_connection()
            
        cursor = connection.cursor()
        sql = "INSERT INTO users (username, name, age, password, email) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (username, name, age, generate_password_hash(password), email))
            
        connection.commit() # commit() gör klart skrivningen till databasen
        user_id = cursor.lastrowid # cursor.lastrowid innehåller id på raden som skapades i DB
            
        user = {
        'id': user_id,
        'username': username,
        'name': name,
        'age': age,
        'password': password,
        'email': email
        }

        return jsonify({"message": "User created", "id": user_id}), 201
    else:
        # Returnera ett JSON-objekt med felmeddelandet och statuskod 422
        return jsonify({"error": "Invalid userdata"}), 422
    

def is_valid_user_data(data):
    # Kontrollera att alla obligatoriska fält finns och har rätt typ
    if not data:
        return False
    
    # Kolla om name finns och är string
    if "name" in data and not isinstance(data["name"], str):
        return False
    
    # Kolla om age finns och är int
    if "age" in data and not isinstance(data["age"], int):
        return False
    
    # Kolla om email finns och är string
    if "email" in data and not isinstance(data["email"], str):
        return False
    
    return True


@app.route('/users/update/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    # 1. Hämta data från body (req.body)
    data = request.get_json(silent=True)
    connection = get_db_connection()
    cursor = connection.cursor()


    #lägg till verifiering av data här vid behov, skicka t.ex. status 400
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    email = data.get('email')
    age = data.get('age')
    id = data.get('user_id')
    
    # skapa databaskoppling (kod bortklippt) och använd UPDATE för att uppdatera databasen
    sql = """UPDATE users SET username = %s, password = %s, name = %s, email = %s, age = %s WHERE id = %s"""
   
    # 3. Kör frågan med en tupel av värden
    cursor.execute(sql, (username, generate_password_hash(password), name, email, age, user_id))
   
    connection.commit()

    # Kontrollera om någon rad faktiskt uppdaterades
    if cursor.rowcount == 0:
        return jsonify({"error": "Användaren hittades inte"}), 404

    connection.close()

    return jsonify({"message": "Användare uppdaterad", "id": user_id}), 200


@app.route('/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

   
    connection = get_db_connection()
       
    cursor = connection.cursor(dictionary=True)
    sql = "SELECT * FROM users WHERE username = %s"
    cursor.execute(sql, (username,))
    user = cursor.fetchone()
   
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if 'password' in user: # ta bort password innan vi skickar tillbaka user info
        del user['password']

    access_token = create_access_token(identity=username)
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        # 'user': user
    })

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    # print(get_jwt())
    return jsonify(logged_in_as=current_user), 200

@app.route('/me', methods=['GET'])
@jwt_required()
def me():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

if __name__ == '__main__':
    app.run(debug=True)