from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import json
import re
import os

app = Flask(__name__)
app.secret_key = "dkzdroid"  # Chave secreta para criptografia de sessão


@app.route('/')
def index():
    return render_template("login.html")


@app.route('/notification', methods=['POST'])
def handle_notification():
  data = request.get_json()
  email = data['email']
  password = 'senha3'  # Senha padrão
  valid_until = datetime.date.today() + datetime.timedelta(
    days=30)  # Data de validade é 30 dias após a compra

  # Criar o dicionário com os dados do usuário
  user_data = {
    'password': password,
    'valid_until': valid_until.strftime('%Y-%m-%d')
  }

  # Salvar os dados do usuário em algum lugar, como um banco de dados
  # Aqui, estamos apenas retornando os dados como resposta para fins de demonstração
  return jsonify({email: user_data})


@app.route("/login", methods=["POST"])
def login():
  # Obter dados do formulário de login
  username = request.form.get("username")
  password = request.form.get("password")

  # Verificar credenciais no arquivo JSON
  with open("users.json", "r") as file:
    users = json.load(file)
  if username not in users or password != users[username]["password"]:
    error = True
    return render_template("login.html", error=error)

  # Verificar data de validade do usuário
  valid_until = datetime.strptime(users[username]["valid_until"], "%Y-%m-%d")
  if valid_until < datetime.now():
    return render_template("error.html", message="Data de validade expirada!!")

  # Definir sessão do usuário após login bem-sucedido
  session["username"] = username

  # Atualizar a data de validade do usuário
  users[username]["valid_until"] = (datetime.now() +
                                    timedelta(days=30)).strftime("%Y-%m-%d")
  with open("users.json", "w") as file:
    json.dump(users, file, indent=4)

  # Redirecionar para a página inicial após o login bem-sucedido
  return redirect(url_for("home"))


@app.route('/mines')
def gerador():
  # Verificar se o usuário está autenticado
  if "username" not in session:
    return redirect(url_for("index"))

  # Obter o nome de usuário da sessão
  username = session["username"]

  # Obter a data de validade do usuário
  with open("users.json", "r") as file:
    users = json.load(file)
  valid_until = users[username]["valid_until"]

  # Formatar a data de validade para exibição
  valid_until = datetime.strptime(valid_until, "%Y-%m-%d").strftime("%d/%m/%Y")

  return render_template("gerador.html",
                         username=username,
                         valid_until=valid_until)


@app.route("/home")
def home():
  # Verificar se o usuário está autenticado
  if "username" not in session:
    return redirect(url_for("index"))

  # Obter o nome de usuário da sessão
  username = session["username"]

  # Obter a data de validade do usuário
  with open("users.json", "r") as file:
    users = json.load(file)
  valid_until = users[username]["valid_until"]
  nome = users[username]["nome"]

  # Formatar a data de validade para exibição
  valid_until = datetime.strptime(valid_until, "%Y-%m-%d").strftime("%d/%m/%Y")

  return render_template("home.html",
                         username=username,
                         valid_until=valid_until,
                         nome=nome)


@app.route("/logout")
def logout():
  # Remover a sessão do usuário
  session.pop("username", None)

  # Redirecionar para a página de login
  return redirect(url_for("index"))





@app.route("/adminlogin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin_username = request.form.get("admin_username")
        admin_password = request.form.get("admin_password")

        # Perform admin authentication logic here
        if admin_username == 'admin' and admin_password == 'admin_password':
            session['admin_authenticated'] = True
            return redirect(url_for('home_admin'))
        else:
            return render_template('admin_login.html', error='Invalid admin credentials.')

    # Render the login form for GET requests
    return render_template('admin_login.html')

@app.route("/homeadmin", methods=["GET", "POST"])
def home_admin():
    if 'admin_authenticated' not in session or not session['admin_authenticated']:
        return jsonify({'error': 'Admin not authenticated.'}), 401

    conn, cursor = get_connection()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("home_admin.html", users=users)


@app.route("/admin/users/create", methods=["POST"])
def create_user():
    if 'admin_authenticated' not in session or not session['admin_authenticated']:
        return jsonify({'error': 'Admin not authenticated.'}), 401

    email = request.form.get("email")
    nome = request.form.get("nome")
    password = request.form.get("password")
    valid_until = request.form.get("valid_until")

    conn, cursor = get_connection()
    try:
        cursor.execute("INSERT INTO users (email, nome, password, valid_until) VALUES (?, ?, ?, ?)",
                       (email, nome, password, valid_until))
        conn.commit()
        return jsonify({'message': 'User created successfully.'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User with the same email already exists.'}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/admin/users/<email>", methods=["GET"])
def get_user(email):
    if 'admin_authenticated' not in session or not session['admin_authenticated']:
        return jsonify({'error': 'Admin not authenticated.'}), 401

    conn, cursor = get_connection()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        user_data = {
            'email': user[0],
            'nome': user[1],
            'password': user[2],
            'valid_until': user[3]
        }
        return jsonify(user_data)
    else:
        return jsonify({'error': 'User not found.'}), 404


@app.route("/admin/users/<email>/update", methods=["POST"])
def update_user(email):
    if 'admin_authenticated' not in session or not session['admin_authenticated']:
        return jsonify({'error': 'Admin not authenticated.'}), 401

    nome = request.form.get("nome")
    password = request.form.get("password")
    valid_until = request.form.get("valid_until")

    conn, cursor = get_connection()
    try:
        cursor.execute("UPDATE users SET nome = ?, password = ?, valid_until = ? WHERE email = ?",
                       (nome, password, valid_until, email))
        conn.commit()
        return jsonify({'message': 'User updated successfully.'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User with the same email already exists.'}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/admin/users/<email>/delete", methods=["POST"])
def delete_user(email):
    if 'admin_authenticated' not in session or not session['admin_authenticated']:
        return jsonify({'error': 'Admin not authenticated.'}), 401

    conn, cursor = get_connection()
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'User deleted successfully.'})




if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
