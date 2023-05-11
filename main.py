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


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
