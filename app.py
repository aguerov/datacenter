from flask import Flask, render_template, request, redirect, url_for, flash, session
from itertools import cycle
from flask_mysqldb import MySQL, MySQLdb
from flask_login import LoginManager, login_user, logout_user
from datetime import timedelta
import bcrypt
import datetime


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskdb'
#app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

@app.route('/sal/<id>', methods = ['POST', 'GET'])
def salida(id):
    
    dt = datetime.datetime.now()
    solohora = dt.hour
    solominuto = dt.minute
    if solohora < 10:
        solohora = ("0%s" % (solohora))
    if solominuto < 10:
        solominuto = ("0%s" % (solominuto))
    hora = ("{}:{}".format(solohora, solominuto))
    
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM visita WHERE id = %s', (id,) )
    data = cur.fetchone()
    cur.close()
    
    return render_template('salida.html', visita = data, hora = hora)

@app.route('/update/<id>', methods=['POST'])
def update_visita(id):
    if request.method == 'POST':
        salida = request.form['hora_salida']
        cur = mysql.connection.cursor()
        cur.execute('UPDATE visita SET salida = %s  WHERE id = %s', (salida, id))
        flash('Salida Marcada, recuerde hacer logout', "warning")
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('home'))
    

@app.route("/" , methods=["GET", "POST"])
def home():
    
    if request.method == "POST":

        fecha = request.form['fecha']
        id_user = session['id_user']
        id_guest = session['id_guest']
        tipo_motivo = request.form['tipo']
        motivo = request.form['motivo']
        entrada = request.form['hora_ingreso']
        salida = request.form['hora_salida']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO visita (id_user, id_guest, tipo_motivo, motivo, fecha, entrada, salida) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (id_user, id_guest, tipo_motivo, motivo, fecha, entrada, salida,))
        mysql.connection.commit()
        # aqui van los demas datos
        return redirect(url_for('home', fecha = fecha))
    else:
        dt = datetime.datetime.now()
        
        solodia = dt.day
        solomes = dt.month
        if solodia < 10:
            solodia = ("0%s" % (solodia))
        if solomes < 10:
            solomes = ("0%s" % (solomes))
        fecha = ("{}-{}-{}".format(dt.year, solomes, solodia))
        fecha2 = ("{}-{}-{}".format(solodia, solomes, dt.year))
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM visita WHERE fecha=%s", (fecha,))
        visitas = cur.fetchall()
        cur.close()
    

        for visita in visitas:

            id_guest = visita['id_guest']    
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM guest WHERE id=%s", (id_guest,))
            curg = cur.fetchone()
            
            cur.close()
            rut_guest = curg['rut_guest']
            nombre_guest = curg['nombre_guest']
            apellidos = curg['apellidos']
            empresa = curg['empresa']
            
            visita["rut_guest"] = rut_guest
            visita["nombre_guest"] = nombre_guest
            visita["apellidos"] = apellidos
            visita["empresa"] = empresa
        
        for visita in visitas:

            empresa = visita['empresa']    
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM empresa WHERE id_empresa=%s", (empresa,))
            cure = cur.fetchone()
            cur.close()
            nom_empresa = cure['nom_empresa']

            id_user = visita['id_user']
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM users WHERE id=%s", (id_user,))
            curu = cur.fetchone()
            cur.close()

            nom_user = curu['user']

            visita["nom_empresa"] = nom_empresa
            visita["nom_user"] = nom_user 
        
        return render_template('home.html', visitas=visitas, fecha = fecha, fecha2= fecha2 )



@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        user = request.form['user']
        password = request.form['password'].encode('utf-8')
        confirm = request.form['confirm'].encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
        if password == confirm:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (name, email, user, password) VALUES (%s,%s,%s,%s)",
                        (name, email, user, hash_password,))
            mysql.connection.commit()
            return redirect(url_for('login'))
        else:
            flash("Las contraseñas deben ser las mismas", "danger")
            return render_template("registro.html")

    return render_template("registro.html")


@app.route('/login', methods=["GET", "POST"])
def login():

    if request.method == "POST":
        usuario = request.form['user']
        password = request.form['password'].encode('utf-8')

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE user=%s", (usuario,))
        user = cur.fetchone()
        cur.close()

        if user is None:
            flash("El Usuario ingresado No Existe", "danger")
            return render_template("login.html")
        else:
            if bcrypt.hashpw(password, user['password'].encode('utf-8')) == user['password'].encode('utf-8'):

                session['name'] = user['name']
                session['user'] = user['user']
                session['id_user'] = user ['id']
                bv = "Bienvenido: "
                bv += user['name']
                flash(bv, "success")
                return render_template("validarut.html")

            else:
                flash("El Password ingresado es Incorrecto", "danger")
                return render_template("login.html")

    else:
        return render_template("login.html")

@app.route('/validarut', methods=["GET", "POST"])
def validarut():
    return render_template("validarut.html")

@app.route('/guest', methods=["GET", "POST"])
def guest():
    dt = datetime.datetime.now()
    solohora = dt.hour
    solominuto = dt.minute
    if solohora < 10:
        solohora = ("0%s" % (solohora))
    if solominuto < 10:
        solominuto = ("0%s" % (solominuto))
        
    hora = ("{}:{}".format(solohora, solominuto))

    solodia = dt.day
    solomes = dt.month

    if solodia < 10:
        solodia = ("0%s" % (solodia))
    if solomes < 10:
        solomes = ("0%s" % (solomes))

        fecha = ("{}-{}-{}".format(dt.year, solomes, solodia))

    if request.method == "POST":
        rut_guest = session['rutv']
        nombre_guest = request.form['nombre_guest']
        apellidos = request.form['apellidos']
        empresa = request.form['empresa']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO guest (rut_guest, nombre_guest, apellidos, empresa) VALUES (%s,%s,%s,%s)", (rut_guest, nombre_guest, apellidos, empresa))
        mysql.connection.commit()
        cur.close()

        if rut_guest:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM guest WHERE rut_guest=%s", (rut_guest,))
            curguest = cur.fetchone()
            cur.close()
            session['id_guest'] = curguest['id']

        if empresa:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM empresa WHERE id_empresa=%s", (empresa,))
            empcur = cur.fetchone()
            nom_empresa = empcur['nom_empresa']
            
            cur.close()
        
        return render_template("ingresodata.html", rutdv=rut_guest, nombre=nombre_guest, apellidos=apellidos, empresa=nom_empresa, fecha=fecha, hora=hora, dis="disabled", autof="autofocus")
    else:
        return render_template("ingresodata.html")

@app.route('/empresav', methods=["GET", "POST"])
def empresav():
    if request.method == "POST":
        empresa = request.form['empresa']
        direccion = request.form['direccion']
        email = request.form['email']
        telefono = request.form['telefono']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("INSERT INTO empresa (nom_empresa, direccion, email, telefono) VALUES (%s,%s,%s,%s)", (empresa, direccion, email, telefono,))
        mysql.connection.commit()
        rutv = session['rutv']
        
        flash("El Rut no posee registro", "warning")
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM empresa ORDER BY nom_empresa')
        data = cur.fetchall()
        cur.close()
        
        return render_template('ingresodata.html', rutdv=rutv, empresas=data)
    else:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM empresa ORDER BY nom_empresa')
        data = cur.fetchall()
        cur.close()
        
        return render_template('empresav.html', empresas=data)

@app.route('/edit/<id>', methods = ['POST', 'GET'])
def get_contact(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM empresa WHERE id_empresa = %s', (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit-empresa.html', empresa = data[0])



@app.route('/updateempresa/<id>', methods=['POST'])
def empresa(id):
    if request.method == 'POST':
        empresa = request.form['empresa']
        direccion = request.form['direccion']
        email = request.form['email']
        telefono = request.form['telefono']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE empresa
            SET nom_empresa = %s,
                direccion = %s,
                email = %s,
                telefono = %s
            WHERE id_empresa = %s
        """, (empresa, direccion, email, telefono, id))
        mysql.connection.commit()
        cur.close()

        flash('Empresa editada correctamente', "warning")
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM empresa ORDER BY nom_empresa')
        data = cur.fetchall()
        cur.close()
        rutv = session['rutv']
        
        return render_template('ingresodata.html', rutdv=rutv, empresas=data)

@app.route('/rutdv', methods=["GET", "POST"])
def rutdv():

    rut = request.form['rut']
    rut = rut.upper()
    rut = rut.replace("-", "")
    rut = rut.replace(".", "")
    aux = rut[:-1]
    dv = rut[-1:]

    revertido = map(int, reversed(str(aux)))
    factors = cycle(range(2, 8))
    s = sum(d * f for d, f in zip(revertido, factors))
    res = (-s) % 11

    if str(res) == dv or dv == "K" or dv == "k" and res == 10:
        dt = datetime.datetime.now()
        solohora = dt.hour
        solominuto = dt.minute
        if solohora < 10:
            solohora = ("0%s" % (solohora))
        if solominuto < 10:
            solominuto = ("0%s" % (solominuto))
        hora = ("{}:{}".format(solohora, solominuto))

        solodia = dt.day
        solomes = dt.month

        if solodia < 10:
            solodia = ("0%s" % (solodia))
        if solomes < 10:
            solomes = ("0%s" % (solomes))

        fecha = ("{}-{}-{}".format(dt.year, solomes, solodia))

        if request.method == "POST":
            rutv = rut
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)   
            cur.execute("SELECT * FROM guest WHERE rut_guest=%s", (rutv,))
            rutcur = cur.fetchone()
            cur.close()
            
            session['rutv'] = rutv
            if rutcur is None:
                flash("El Rut no posee registro", "warning")
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM empresa ORDER BY nom_empresa')
                data = cur.fetchall()
                cur.close()

                return render_template('ingresodata.html', rutdv=rutv, fecha=fecha, hora=hora, empresas=data)
            else:
                rutv = rutcur['rut_guest']
                session['id_guest'] = rutcur['id']
                nombre = rutcur['nombre_guest']
                apellidos = rutcur['apellidos']
                empresa = rutcur['empresa']
                if empresa:
                    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cur.execute(
                        "SELECT * FROM empresa WHERE id_empresa=%s", (empresa,))
                    empcur = cur.fetchone()
                    nom_empresa = empcur['nom_empresa']
                   
                    cur.close()
                    return render_template("ingresodata.html", rutdv=rutv, nombre=nombre, apellidos=apellidos, empresa=nom_empresa, fecha=fecha, hora=hora, dis="disabled", autof="autofocus")        
            return render_template("ingresodata.html", rutdv=rutv, nombre=nombre, apellidos=apellidos, empresa=nom_empresa, fecha=fecha, hora=hora, dis="disabled", autof="autofocus")

    else:
        flash("El Rut ingresado es Incorrecto", "danger")
        return render_template("validarut.html", rutdv=rut)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(seconds=40)

if __name__ == '__main__':
    app.secret_key = "^A%DJAJU^JJ123"
    app.run(debug=True)