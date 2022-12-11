import os
import uuid
from flask import Flask, session,render_template,request, Response, redirect, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from db import db_init, db
from models import  User, Product
from datetime import datetime
from flask_session import Session
from helpers import login_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db_init(app)

## Configuración de sesión para ocupar el sistema de archivos
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

## Ruta de archivo
@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)

## Acá se registra como vendedor
@app.route("/signup", methods=["GET","POST"])
def signup():
	if request.method=="POST":
		session.clear()
		password = request.form.get("password")
		repassword = request.form.get("repassword")
		if(password!=repassword):
			return render_template("error.html", message="Las contraseñas no coinciden!")

		#hash password
		pw_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

		fullname = request.form.get("fullname")
		username = request.form.get("username")

		## Acá se guardan en la base de datos los usuarios
		new_user =User(fullname=fullname,username=username,password=pw_hash)
		try:
			db.session.add(new_user)
			db.session.commit()
		except:
			return render_template("error.html", message="El username ya está en uso!")
		return render_template("login.html", msg="Cuenta creada!")
	return render_template("signup.html")

##  Iniciando sesión como vendedor
@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method=="POST":
		session.clear()
		username = request.form.get("username")
		password = request.form.get("password")
		result = User.query.filter_by(username=username).first()
		#
		print(result)
		# Revisando si el usuario existe y los datos son correctos
		if result == None or not check_password_hash(result.password, password):
			return render_template("error.html", message="Username/Contraseña inválido")

		## Recordando qué usurio inició sesión,cual está activo
		session["username"] = result.username
		return redirect("/home")
	return render_template("login.html")

## Cerrando sesión
@app.route("/logout")
def logout():
	session.clear()
	return redirect("/login")

## Viendo todos lod productos
@app.route("/")

def index():
	rows = Product.query.all()
	return render_template("index.html", rows=rows)

## Interfaz al inicar como vendedor para agregar o editar productos
@app.route("/home", methods=["GET", "POST"], endpoint='home')
@login_required
def home():
	if request.method == "POST":
		image = request.files['image']
		filename = str(uuid.uuid1())+os.path.splitext(image.filename)[1]
		image.save(os.path.join("static/images", filename))
		category= request.form.get("category")
		name = request.form.get("pro_name")
		description = request.form.get("description")
		price_range = request.form.get("price_range")
		comments = request.form.get("comments")
		new_pro = Product(category=category,name=name,description=description,price_range=price_range,comments=comments, filename=filename, username=session['username'])
		db.session.add(new_pro)
		db.session.commit() 
		rows = Product.query.filter_by(username=session['username'])
		return render_template("home.html", rows=rows, message="Producto Agregado!")

	rows = Product.query.filter_by(username=session['username'])
	return render_template("home.html", rows=rows)

## Cuando se quiere editar los productos esta función se ejecuta
@app.route("/edit/<int:pro_id>", methods=["GET", "POST"], endpoint='edit')
@login_required
def edit(pro_id):
	# Seleccionando solo el producto que se quiere editar de la base de datos
	result = Product.query.filter_by(pro_id = pro_id).first()
	if request.method == "POST":
		#Erro que se ejecuta cuando alguien que no es el mero vendedor quiere editar los productos,puede que la quite

		if result.username != session['username']:
			return render_template("error.html", message="No estás autorizado para editar este producto")
		category= request.form.get("category")
		name = request.form.get("pro_name")
		description = request.form.get("description")
		price_range = request.form.get("price_range")
		comments = request.form.get("comments")
		result.category = category
		result.name = name
		result.description = description
		result.comments = comments
		result.price_range = price_range
		db.session.commit()
		rows = Product.query.filter_by(username=session['username'])
		return render_template("home.html", rows=rows, message="Producto editado")
	return render_template("edit.html", result=result)