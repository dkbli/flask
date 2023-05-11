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



if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
