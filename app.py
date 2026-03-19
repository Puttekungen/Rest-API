from mysql.connector import Error
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, get_jwt, jwt_required, get_jwt_identity



# Skapar Flask-applikationen    
app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key_here'  # TODO: Ändra detta till en slumpmässig hemlig nyckel
# Initierar JWT-hantering för inloggning och skyddade endpoints
jwt = JWTManager(app)

# Databaskonfiguration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Ändra detta till ditt MySQL-användarnamn
    'password': '',  # Ändra detta till ditt MySQL-lösenord
    'database': 'inlamning_1'
}
# Hjälpfunktion som skapar en ny databasanslutning
def get_db_connection():
    """Skapa och returnera en databasanslutning"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Fel vid anslutning till MySQL: {e}")
        return None

# Global felhanterare som fångar oväntade exceptions. men är designad för att säga till när man försöker skapa en användare med redan existerande username eller email, eftersom dessa fält är unika i databasen.
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({'error': 'User or Email already in use'}), 500

# Route: Visar enkel API-dokumentation i HTML
@app.route('/', methods=['GET'])
def index():
    return '''<h1>Documentation</h1>
    <ul><li>kräver giltig bearer token GET /users - returnerar alla användare</li></ul>
    <ul><li>kräver giltig bearer token GET /users/{id} - returnerar en specifik användare med id</li></ul>
    <ul><li>kräver giltig bearer token GET /users/age/{age} - returnerar alla användare med en viss ålder</li></ul>
    <ul><li>POST /create - skapar en ny användare. Accepterar JSON objekt på formatet {"username": "unikt namn", "name": "ditt namn", "age": din ålder, "password": "ditt lösenord", "email": "unik email"}</li></ul>
    <ul><li>kräver giltig bearer token PUT /users/update/{id} - uppdaterar en användare med id</li></ul>
    <ul><li>POST /login - loggar in en användare och returnerar en JWT-token, använd formatet {"username": "Ditt username", "password": "ditt password"}</li></ul>
    <ul><li>kräver giltig bearer token GET /protected - den visar vilken användare man är inloggad som</li></ul>
    '''


# Route: Hämtar alla användare (kräver JWT)
@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    sql = "SELECT username, name, email, age FROM users"
    cursor.execute(sql)
    users = cursor.fetchall()
    connection.close()
   
    return jsonify(users)


# Route: Hämtar en specifik användare via ID (kräver JWT)
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
    connection.close()

    user.pop('password')
    if not user: # saknades personen i databasen?
        return jsonify({'error': 'User not found'}), 404
    else:
        return jsonify(user)
       

# Route: Hämtar användare med en viss ålder (kräver JWT)
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
    connection.close()
   
    if not user: # saknades personen i databasen?
        return jsonify({'error': 'User not found'}), 404
    else:
        return jsonify(user)



# Route: Skapar en ny användare
@app.route('/create', methods=['POST'])
def creating_user():
    data = request.get_json(silent=True)

    if is_valid_user_data(data):
        # Logik för databas här...

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

        connection.close()

        return jsonify({"message": "User created", "id": user_id}), 201
    else:
        # Returnera ett JSON-objekt med felmeddelandet och statuskod 422
        return jsonify({"error": "Invalid userdata"}), 422
    

# Hjälpfunktion: validerar inkommande user-data innan insert/update. Name måste våra en sträng, age måste vara ett heltal, email måste vara en sträng
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


# Route: Uppdaterar en användare via ID (kräver JWT)
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
        connection.close()
        return jsonify({"error": "Användaren hittades inte"}), 404

    cursor = connection.cursor(dictionary=True)
    sql = "SELECT * FROM users WHERE id = %s"
    cursor.execute(sql, (user_id,))
    user = cursor.fetchone()

    connection.close()
    return jsonify(user), 200


# Route: Loggar in användare och returnerar JWT-token
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
        connection.close()
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if 'password' in user: # ta bort password innan vi skickar tillbaka user info
        del user['password']

    access_token = create_access_token(identity=username)
    connection.close()
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
    })


# Route: Enkel test-endpoint för att verifiera JWT
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# Startar appen lokalt i debug-läge
if __name__ == '__main__':
    app.run(debug=True)