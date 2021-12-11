from flask import Flask, render_template, redirect, url_for, flash,request,session
import pymysql
from registerForm import RegisterForm, LoginForm, AddVictim,RequestResetForm,ResetPasswordForm
import base64
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import smtplib, ssl
from email.header import Header
from email.utils import formataddr
from email.message import EmailMessage
from flask_mail import Mail,Message

# import os
# generating screte key:
# print(os.urandom(32).hex())


# Now create flask application object
app = Flask(__name__)
app.config['SECRET_KEY'] = '2358817b22c7299f8f9a3147bb91316708d784a6b5d900500f790abc5b1a5cfd'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'istm6210ias@gmail.com'
app.config['MAIL_PASSWORD'] = 'IAS@ISTM'
mail = Mail(app)

conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    passwd="ying1234",
    port=3306,
    db="test",
)
msg = ""

# @app.route('/')
# def hello_world():
#     return "<h1>Hello world!!!Ying</h1>"

# @app.route('/about/<name>')
# def about(name):
#     return f'<h1>Hello world!!!{name}</h1>'
def write_file(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)


@app.route('/victims', methods=['GET', 'POST'])
def victim_page():
    form = AddVictim()
    if 'loggedin' in session:
        cursor = conn.cursor()
        sql = f"""
            select * from victims
        """
        victims = []
        singleVictim = {}
        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            for row in data:
                if row[1] != None:
                    image = row[5].decode('utf-8')
                    singleVictim = {"ID": row[0],"FirstName":row[1], "LastName":row[2], 
                    "Photo": image,"Email":row[4], "Phone": row[3]}
                    victims.append(singleVictim)
                else:
                    # image = image.decode('utf-8')
                    singleVictim = {"ID": row[0],"FirstName":row[1], "LastName":row[2], 
                    "Photo": "","Email":row[4], "Phone": row[3]}
                    victims.append(singleVictim)
        except Exception as e:
            print(e)
            print("Fail to load data!")

        if 'loggedin' in session and request.method == 'POST': 
            if 'btnDelete' in request.form:
                cursor = conn.cursor()
                sql_update = f""" 
                Delete from victims
                where victim_id = %s
                """
                victim_id  = request.form["ID"]
                try:
                    cursor.execute(sql_update, victim_id)
                    conn.commit()
                    print("Delete successfully!")
                    flash(f"Victim {victim_id}: removed succussfully!", category='success')
                    return redirect(request.url) 
                except Exception as e:
                    print(e)
                    conn.rollback()
                    print("Fail to update data!")
            elif 'btnEdit' in request.form:
                cursor = conn.cursor()
                sql_update = f""" 
                UPDATE victims set
                phone=%s, email=%s where victim_id = %s
                """
                update_id  = request.form["ID"]
                update_phone  = request.form["Phone"]
                update_email  = request.form["Email"]
                try:
                    update_data = (update_phone,update_email,update_id)
                    cursor.execute(sql_update, update_data)
                    conn.commit()
                    print("update successfully!")
                    flash(f"Victim {update_id}: updated succussfully!", category='success')
                    return redirect(request.url) 
                except Exception as e:
                    print(e)
                    conn.rollback()
                    print("Fail to update data!")
            else:
                user_firstname = form.user_firstname.data
                user_lastname = form.user_lastname.data
                phone = form.phone.data
                email_address = form.email_address.data
                photo = form.photo.data
                if photo != '':      
                    image = photo  
                    photo_encoded = base64.b64encode(image.read())
                # insert data into database
                cursor = conn.cursor()
                sql_insert = f""" 
                INSERT INTO victims
                (firstName, lastName, phone, email, photo) VALUES (%s,%s,%s,%s,%s)
                """
                try:
                    insert_data = (user_firstname, user_lastname, phone, 
                    email_address, photo_encoded)
                    cursor.execute(sql_insert, insert_data)
                    conn.commit()
                    print("Add successfully!")
                    flash("New victim added succussfully!",category='success')
                    return redirect(request.url) 
                except Exception as e:
                    print(e)
                    conn.rollback()
                    print("Fail to update data!")
    else:
        return redirect(url_for('login_page'))
    return render_template('victims.html', form=form, victims=victims)

@app.route('/')  
@app.route('/home', methods=['GET', 'POST'])
def home_page():
    if 'loggedin' in session and request.method == 'POST': 
        if request.form['btn'] == 'Accept':
            cursor = conn.cursor()
            sql_update = f""" 
            UPDATE cases set
            status="In progress" where case_id = %s
            """
            update_id  = request.form["ID"]
            try:
                update_data = (update_id)
                cursor.execute(sql_update, update_data)
                conn.commit()
                print("update successfully!")
                try:
                    cursor_id_cases = conn.cursor()
                    sql = f"""
                        select victim_id from cases
                        where case_id = %s
                    """
                    cursor_id_cases.execute(sql,update_id)
                    data_id_cases = cursor_id_cases.fetchone()
                    data_id_cases[0]
                    if data_id_cases[0] != None:
                        try:
                            cursor_email = conn.cursor()
                            sql = f"""
                                select victims.email from victims
                                LEFT JOIN cases ON victims.victim_id = cases.victim_id
                                where case_id = %s
                            """
                            cursor_email.execute(sql,update_id)
                            data_email = cursor_email.fetchone()
                            victim_email = data_email[0]

                            #####  sending alert email to police ####
                            smtp_server = "smtp.gmail.com"
                            port = 587  # For starttls
                            sender_email = "istm6210ias@gmail.com"
                            password = "IAS@ISTM"
                            receiver_email = victim_email
                            # mailing_list = ["user1@company.com"]
                            subject = 'Case accepted'
                            msg = EmailMessage()
                            msg.add_alternative("""\
                                <!doctype html>
                                <html>
                                <body style="background-color: #f6f6f6; -webkit-font-smoothing: antialiased; line-height: 1.4; margin: 0; padding: 0; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;">
                                    <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%; background-color: #f6f6f6;">
                                    <tr>
                                        <td style="vertical-align: top;">&nbsp;</td>
                                        <td style="display: block; Margin: 0 auto; max-width: 580px; padding: 10px; width: 580px;">
                                        <div style="box-sizing: border-box; display: block; Margin: 0 auto; max-width: 580px; padding: 10px;">

                                            <table role="presentation" style="border-collapse: separate;  width: 100%; background: #ffffff; border-radius: 3px;">
                                            <tr>
                                                <td style="vertical-align: top; box-sizing: border-box; padding: 20px;">
                                                <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%;">
                                                    <tr>
                                                    <td style="vertical-align: top;">
                                                        <p style="margin: 0; Margin-bottom: 15px;">Hi there,</p>
                                                        <p style="margin: 0; Margin-bottom: 15px;">
                                                            Thanks for subscribing IAS. Your case was <i style="color:red; font-weight: bold;"> ACCEPTED</i> by IAS.
                                                        </p>
                                                    </p>
                                                        <p style="margin: 0; Margin-bottom: 15px;">
                                                            If you have any questions, please contact us!
                                                        </p>
                                                    </td>
                                                    </tr>
                                                </table>
                                                </td>
                                            </tr>
                                            </table>
                                            <div style="clear: both; Margin-top: 10px; text-align: center; width: 100%;">
                                            <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%;">
                                                <tr>
                                                    <td style="vertical-align: top; padding-bottom: 10px; padding-top: 10px; color: #999999; text-align: center;">
                                                        Intelligent alert system
                                                    </td>
                                                </tr>
                                                <tr>
                                                <td style="vertical-align: top; padding-bottom: 10px; padding-top: 10px; color: #999999; text-align: center;">
                                                    <span style="color: #999999; text-align: center;">Intelligent alert system, GWU ISTM 6210, Washington DC 20052</span>
                                                </td>
                                                </tr>
                                            </table>
                                            </div>
                                        </div>
                                        </td>
                                        <td style="vertical-align: top;">&nbsp;</td>
                                    </tr>
                                    </table>
                                </body>
                                </html>
                                """, subtype='html')
                            msg['Subject'] = subject
                            msg['From'] = formataddr((str(Header('Intelligent Alert System', 
                                                                    'utf-8')), sender_email))
                            # msg['From'] = sender_email
                            msg['To'] = receiver_email
                            message = msg.as_string()
                            # Create a secure SSL context
                            context = ssl.create_default_context()

                            # Try to log in to server and send email
                            try:
                                server = smtplib.SMTP(smtp_server,port)
                                server.ehlo() # Can be omitted
                                server.starttls(context=context) # Secure the connection
                                server.ehlo() # Can be omitted
                                server.login(sender_email, password)
                                server.sendmail(sender_email, receiver_email, message)
                            except Exception as e:
                                # Print any error messages to
                                print(e)
                            finally:
                                server.quit() 
                        except Exception as e:
                            print(e)
                            print("Fail to load data!")
                except Exception as e:
                    print(e)
                    print("Fail to load data!")
                return redirect(url_for('home_page'))
            except Exception as e:
                print(e)
                conn.rollback()
                print("Fail to update data!")
            
        else:
            cursor = conn.cursor()
            sql_update = f""" 
            UPDATE cases set
            status="Rejected" where case_id = %s
            """
            update_id  = request.form["ID"]
            try:
                update_data = (update_id)
                cursor.execute(sql_update, update_data)
                conn.commit()
                print("update successfully!")
                try:
                    cursor_id_cases = conn.cursor()
                    sql = f"""
                        select victim_id from cases
                        where case_id = %s
                    """
                    cursor_id_cases.execute(sql,update_id)
                    data_id_cases = cursor_id_cases.fetchone()
                    if data_id_cases[0] != None:
                        try:
                            cursor_email = conn.cursor()
                            sql = f"""
                                select victims.email from victims
                                LEFT JOIN cases ON victims.victim_id = cases.victim_id
                                where case_id = %s
                            """
                            cursor_email.execute(sql,update_id)
                            data_email = cursor_email.fetchone()
                            victim_email = data_email[0]

                            #####  sending alert email to police ####
                            smtp_server = "smtp.gmail.com"
                            port = 587  # For starttls
                            sender_email = "istm6210ias@gmail.com"
                            password = "IAS@ISTM"
                            receiver_email = victim_email
                            # mailing_list = ["user1@company.com"]
                            subject = 'Case rejected'
                            msg = EmailMessage()
                            msg.add_alternative("""\
                                <!doctype html>
                                <html>
                                <body style="background-color: #f6f6f6; -webkit-font-smoothing: antialiased; line-height: 1.4; margin: 0; padding: 0; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;">
                                    <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%; background-color: #f6f6f6;">
                                    <tr>
                                        <td style="vertical-align: top;">&nbsp;</td>
                                        <td style="display: block; Margin: 0 auto; max-width: 580px; padding: 10px; width: 580px;">
                                        <div style="box-sizing: border-box; display: block; Margin: 0 auto; max-width: 580px; padding: 10px;">

                                            <table role="presentation" style="border-collapse: separate;  width: 100%; background: #ffffff; border-radius: 3px;">
                                            <tr>
                                                <td style="vertical-align: top; box-sizing: border-box; padding: 20px;">
                                                <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%;">
                                                    <tr>
                                                    <td style="vertical-align: top;">
                                                        <p style="margin: 0; Margin-bottom: 15px;">Hi there,</p>
                                                        <p style="margin: 0; Margin-bottom: 15px;">
                                                            Thanks for subscribing IAS. Your case was <i style="color:red; font-weight: bold;"> REJECTED</i> by IAS.
                                                        </p>
                                                    </p>
                                                        <p style="margin: 0; Margin-bottom: 15px;">
                                                            If you have any questions, please contact us!
                                                        </p>
                                                    </td>
                                                    </tr>
                                                </table>
                                                </td>
                                            </tr>
                                            </table>
                                            <div style="clear: both; Margin-top: 10px; text-align: center; width: 100%;">
                                            <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse: separate; width: 100%;">
                                                <tr>
                                                    <td style="vertical-align: top; padding-bottom: 10px; padding-top: 10px; color: #999999; text-align: center;">
                                                        Intelligent alert system
                                                    </td>
                                                </tr>
                                                <tr>
                                                <td style="vertical-align: top; padding-bottom: 10px; padding-top: 10px; color: #999999; text-align: center;">
                                                    <span style="color: #999999; text-align: center;">Intelligent alert system, GWU ISTM 6210, Washington DC 20052</span>
                                                </td>
                                                </tr>
                                            </table>
                                            </div>
                                        </div>
                                        </td>
                                        <td style="vertical-align: top;">&nbsp;</td>
                                    </tr>
                                    </table>
                                </body>
                                </html>
                                """, subtype='html')
                            msg['Subject'] = subject
                            msg['From'] = formataddr((str(Header('Intelligent Alert System', 
                                                                    'utf-8')), sender_email))
                            # msg['From'] = sender_email
                            msg['To'] = receiver_email
                            message = msg.as_string()
                            # Create a secure SSL context
                            context = ssl.create_default_context()

                            # Try to log in to server and send email
                            try:
                                server = smtplib.SMTP(smtp_server,port)
                                server.ehlo() # Can be omitted
                                server.starttls(context=context) # Secure the connection
                                server.ehlo() # Can be omitted
                                server.login(sender_email, password)
                                server.sendmail(sender_email, receiver_email, message)
                            except Exception as e:
                                # Print any error messages
                                print(e)
                            finally:
                                server.quit() 
                        except Exception as e:
                            print(e)
                            print("Fail to load data!")
                except Exception as e:
                    print(e)
                    print("Fail to load data!")
                return redirect(url_for('home_page'))
            except Exception as e:
                print(e)
                conn.rollback()
                print("Fail to update data!")
    
    if 'loggedin' in session:
        # User is loggedin show them the home page
        msg = "Welcome back, " + session['firstname']
        cases = []
        newCases = {}
        cursor = conn.cursor()
        sql = f"""
            select * from cases
            where status = "Detected"
        """
        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            for row in data:
                # print("Id = ", row[0], )
                if row[1] != None:
                    image = row[1].decode('utf-8')
                    # image = image.decode('utf-8')
                    newCases = {"ID": row[0],"Time":row[2], "Location":row[3], 
                    "Image": image,"Status":row[4]}
                    cases.append(newCases)
                    # print(cases)
                else:
                    # image = image.decode('utf-8')
                    newCases = {"ID": row[0],"Time":row[2], "Location":row[3], 
                    "Image": "","Status":row[4]}
                    cases.append(newCases)
                # id = row[0]
        except Exception as e:
            print(e)
            print("Fail to load data!")
            
        return render_template('home.html', firstname= msg,show_modal=True, cases = cases)
    # User is not loggedin redirect to login page
    else:
        msg = "Guest user, please login"
        return render_template('home.html', firstname=msg)
    
    # return render_template("home.html")

# reports from database

@app.route('/reports',methods=['GET','POST'])
def reports():
    if 'loggedin' in session and request.method == 'POST': 
        if 'btnEdit' in request.form:
            cursor = conn.cursor()
            sql_update = f""" 
            UPDATE cases set
            Status=%s, Comments=%s where case_id = %s
            """
            update_id  = request.form["ID"]
            update_comments  = request.form["Comments"]
            try:
                update_data = ("Done",update_comments,update_id)
                cursor.execute(sql_update, update_data)
                conn.commit()
                print("update successfully!")
                flash(f"Case {update_id}: updated succussfully!",category='success')
                return redirect(request.url)
            except Exception as e:
                print(e)
                conn.rollback()
                print("Fail to update data!")
        else:
            cursor = conn.cursor()
            sql_update = f""" 
            Delete from cases
            where case_id = %s
            """
            case_id  = request.form["ID"]
            try:
                cursor.execute(sql_update, case_id)
                conn.commit()
                print("Delete successfully!")
                flash(f"Case {case_id}: removed succussfully!",category='success')
                return redirect(request.url) 
            except Exception as e:
                print(e)
                conn.rollback()
                print("Fail to update data!")
    if 'loggedin' in session:
        cursor = conn.cursor()
        sql = f"""
            select * from cases
        """
        cases = []
        singleCase = {}
        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            for row in data:
                if row[1] != None:
                    # print("Id = ", row[0], )
                    image = row[1].decode('utf-8')
                    # image = image.decode('utf-8')
                    singleCase = {"ID": row[0],"Time":row[2], "Location":row[3], 
                    "Image": image,"Status":row[4],"VictimID": row[5],"Comments": row[6]}
                    cases.append(singleCase)
                    # print(cases)
                else:
                    # image = image.decode('utf-8')
                    singleCase = {"ID": row[0],"Time":row[2], "Location":row[3], 
                    "Image": "","Status":row[4],"VictimID": row[5], "Comments": row[6]}
                    cases.append(singleCase)
                # id = row[0]
        except Exception as e:
            print(e)
            print("Fail to load data!")
        # finally:
        #     conn.close()

        return render_template("reports.html", cases = cases)

    return redirect(url_for('login_page'))
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if 'loggedin' in session:
        return redirect(url_for('home_page'))
    else:
        form = RegisterForm()
        if request.method == 'POST': 
            username = form.username.data
            user_firstname = form.user_firstname.data
            user_lastname = form.user_lastname.data
            phone = form.phone.data
            email_address = form.email_address.data
            password = form.password.data
            confirm_password = form.confirmed_password.data
            photo = request.files['photo']


            # check existing user
            sql_check_user = f""" 
                SELECT * FROM user WHERE userName=%s
            """
            cursor_user = conn.cursor()
            cursor_user.execute(sql_check_user, username)
            count_user = cursor_user.rowcount
            if count_user == 0:
                sql_check_user = f""" 
                SELECT * FROM user WHERE email=%s
                """
                cursor_email = conn.cursor()
                cursor_email.execute(sql_check_user, email_address)
                count_email = cursor_email.rowcount
                if count_email == 0:
                    if password == confirm_password:
                        if photo.filename != '':      
                            image = request.files['photo']  
                            photo_encoded = base64.b64encode(image.read())
                        # insert data into database
                        cursor = conn.cursor()
                        sql_insert = f""" 
                        INSERT INTO user
                        (userName, firstName, lastName, phone, email, password, photo) VALUES (%s,%s,%s,%s,%s,%s,%s)
                        """
                        try:
                            insert_data = (username, user_firstname, user_lastname, phone, 
                            email_address, password, photo_encoded)
                            cursor.execute(sql_insert, insert_data)
                            conn.commit()
                            print("Register successfully!")
                            flash("Register Succussfully!", category='success')
                            return redirect(request.url) 
                            # if form.validate_on_submit():
                            #     return redirect(url_for('login'))
                        except Exception as e:
                            print(e)
                            conn.rollback()
                            print("Fail to Register!")
                            flash("Fail to register!", category='danger')
                            return redirect(request.url)
                    else: 
                        flash("Passwords not matching", category='danger')
                        return redirect(request.url) 
                else:
                    flash(f"Email ({email_address}) already in our records!", category='danger')
                    return redirect(request.url) 
            else:
                flash(f"User name ({username}) already in our records!", category='danger')
                return redirect(request.url) 
    return render_template('register.html', form=form)



#Login page
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if 'loggedin' in session:
        return redirect(url_for('home_page'))
    else:
        form = LoginForm()
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
            userdic = {}
            list = []
            user_inputAccount = form.username.data
            user_inputPassword= form.password.data
            cursor = conn.cursor()
            sql = f"""
                select * from user
                where userName = %s and password = %s
            """
            select_user = (user_inputAccount, user_inputPassword)
            try:
                cursor.execute(sql,select_user)
                data = cursor.fetchall()
                for row in data:
                    if row[7] != None:
                        userimage = row[7].decode('utf-8')
                        userdic = {"UserID": row[0],"UserName": row[1], "FirstName": row[2],
                        "LastName": row[3], "Phone": row[4], "Email": row[5],
                        "UserImage": userimage}
                        list.append(userdic)
                        if list !="":
                            session['loggedin'] = True
                            session['id'] = userdic['UserID']
                            session['firstname'] = userdic['FirstName']
                            session['lastname'] = userdic['LastName']
                            session['username'] = userdic['UserName']
                            flash(f'Welcome back! You are logged in as: ' + userdic['UserName'], category='success')
                            return redirect(url_for('home_page'))
                        else:
                            flash('The username or password that you entered does not match our records.', category='danger')
                            return redirect(request.url)
                    else:
                        userdic = {"UserID": row[0],"UserName": row[1], "FirstName": row[2],
                        "LastName": row[3], "Phone": row[4], "Email": row[5],
                        "UserImage": ""}
                        list.append(userdic)
                        if list !="":
                            session['loggedin'] = True
                            session['id'] = userdic['UserID']
                            session['firstname'] = userdic['FirstName']
                            session['lastname'] = userdic['LastName']
                            session['username'] = userdic['UserName']
                            flash(f'Welcome back! You are logged in as: ' + userdic['UserName'], category='success')
                            return redirect(url_for('home_page'))
                        else:
                            flash('The username or password that you entered does not match our records.', category='danger')
                            return redirect(request.url)
            except Exception as e:
                print(e)
                print("Fail to load data!")

            flash('The username or password that you entered does not match our records.', category='danger')
        return render_template("login.html", form=form)

@app.route('/user_account_page', methods=['GET', 'POST'])
def account():
    userssss={}
    userlist=[]
    if 'loggedin' in session and request.method == 'POST': 
        if request.form['btnEditUser'] == 'Edit':
            cursor = conn.cursor()
            sql_update = f""" 
            UPDATE user set
            phone=%s,email=%s where user_id = %s
            """
            update_id  = session["id"]
            update_phone  = request.form["Phone"]
            update_email  = request.form["Email"]
            try:
                update_data = (update_phone,update_email,update_id)
                cursor.execute(sql_update, update_data)
                conn.commit()
                print("update successfully!")
                flash("Your account updated succussfully!",category='success')
                return redirect(request.url)
            except Exception as e:
                print(e)
                conn.rollback()
                print("Fail to update data!")
        if request.form['btnEditUser'] == 'Submit':
            photo = request.files['photo']
            if photo.filename != '':      
                image = request.files['photo']  
                photo_encoded = base64.b64encode(image.read())
                cursor = conn.cursor()
                sql_update = f""" 
                UPDATE user set
                photo=%s where user_id = %s
                """
                try:
                    update_data = (photo_encoded, session['id'])
                    cursor.execute(sql_update, update_data)
                    conn.commit()
                    flash("Your image updated succussfully!",category='success')
                    return redirect(request.url)
                except Exception as e:
                    print(e)
                    conn.rollback()
                    print("Fail to update data!")
    if 'loggedin' in session:
        cursor = conn.cursor()
        sql = f"""
            select * from user
            where user_id = %s
        """
        cursor.execute(sql, (session['id']))
        account = cursor.fetchall()
        for row in account:
            if row[7] != None:
                userimage = row[7].decode('utf-8')
                userssss = {"UserID": row[0],"UserName": row[1], "FirstName": row[2],
                "LastName": row[3], "Phone": row[4], "Email": row[5],
                "UserImage": userimage}
                userlist.append(userssss)
                return render_template('user_account.html', account=userlist)
            else:
                userssss = {"UserID": row[0],"UserName": row[1], "FirstName": row[2],
                "LastName": row[3], "Phone": row[4], "Email": row[5],
                "UserImage": ""}
                userlist.append(userssss)
                return render_template('user_account.html', account=userlist)

        # Show the profile page with account info
    return redirect(url_for('login_page'))
        # Show the profile page with account info
    # User is not loggedin redirect to login page
        # if form.validate_on_submit():
        # file = form.image.data
        # my_string = base64.b64encode(file.read())

        # cursor = conn.cursor()
        # sql_insert = f""" 
        #     Update user set
        #     photo=%s where userName = %s
        # """
        # try:
        #     cursor.execute(sql_insert, my_string)
        #     conn.commit()
        #     print("insert successfully!")
        # except Exception as e:
        #     print(e)
        #     conn.rollback()
        #     print("Fail to insert data!")
        # finally:
        #     conn.close()

        # return f'Filename: { my_string }'
        # return render_template("user_account.html")

@app.route('/camera', methods=['GET', 'POST'])
def camera():
    if 'loggedin' in session:
        cursor = conn.cursor()
        sql = f"""
            select * from camera
        """
        cameras = []
        singleCamera = {}
        try:
            cursor.execute(sql)
            data = cursor.fetchall()
            for row in data:
                singleCamera = {"ID": row[0],"Location":row[1], "MonitoredBy":row[2], "Status":row[3]}
                cameras.append(singleCamera)
        except Exception as e:
            print(e)
            print("Fail to load data!")

        if 'loggedin' in session and request.method == 'POST': 
            if 'btnDelete' in request.form:
                cursor = conn.cursor()
                sql_update = f""" 
                Delete from camera
                where camera_id = %s
                """
                delete_id  = request.form["ID"]
                try:
                    cursor.execute(sql_update, delete_id)
                    conn.commit()
                    print("Delete successfully!")
                    flash(f"Camera {delete_id}: removed succussfully!",category='success')
                    return redirect(request.url) 
                except Exception as e:
                    print(e)
                    conn.rollback()
                    print("Fail to delete data!")
            elif 'btnAdd' in request.form:
                cursor = conn.cursor()
                sql_update = f""" 
                INSERT INTO camera
                (location, monitoredBy, status) VALUES (%s,%s,%s)
                """
                Location  = request.form["Location"]
                MonitoredBy  = request.form["MonitoredBy"]
                try:
                    update_data = (Location,MonitoredBy,"OFF")
                    cursor.execute(sql_update, update_data)
                    conn.commit()
                    print("insert successfully!")
                    flash("New camera added successfully!", category='success')
                    return redirect(request.url)
                except Exception as e:
                    print(e)
                    conn.rollback()
                    print("Fail to insert data!")
            elif 'btnEdit' in request.form:
                cursor = conn.cursor()
                sql_update = f""" 
                UPDATE camera set
                location=%s where camera_id = %s
                """
                update_id  = request.form["ID"]
                update_location  = request.form["Location"]
                try:
                    update_data = (update_location,update_id)
                    cursor.execute(sql_update, update_data)
                    conn.commit()
                    print("update successfully!")
                    flash(f"Camera {update_id}: updated successfully!", category='success')
                    return redirect(request.url)
                except Exception as e:
                    print(e)
                    conn.rollback()
                    print("Fail to update data!")
            else:
                if request.form["Switch"] == "ON":
                    cursor = conn.cursor()
                    sql_update = f""" 
                    UPDATE camera set
                    monitoredBy=%s, status=%s where camera_id = %s
                    """
                    update_id  = request.form["ID"]
                    name = session['firstname'] + " " + session['lastname']
                    update_statement = (name,"OFF",update_id)
                    try:
                        cursor.execute(sql_update, update_statement)
                        conn.commit()
                        print("Update successfully!")
                        flash(f"Camera {update_id} is now off!", category='danger')
                        return redirect(request.url) 
                    except Exception as e:
                        print(e)
                        conn.rollback()
                        print("Fail to Update data!")
                else:
                    cursor = conn.cursor()
                    sql_update = f""" 
                    UPDATE camera set
                    monitoredBy=%s, status=%s where camera_id = %s
                    """
                    update_id  = request.form["ID"]
                    name = session['firstname'] + " " + session['lastname']
                    update_statement = (name, "ON",update_id)
                    try:
                        cursor.execute(sql_update, update_statement)
                        conn.commit()
                        print("Update successfully!")
                        flash(f"Camera {update_id} is now on!", category='success')
                        return redirect(request.url) 
                    except Exception as e:
                        print(e)
                        conn.rollback()
                        print("Fail to Update data!")
    else:
        return redirect(url_for('login_page'))
    return render_template('camera.html', cameras = cameras)

@app.route('/resetpassword',methods=['GET', 'POST'])
def resetpassword():
    form = RequestResetForm()
    if 'loggedin' in session:
        return redirect(url_for('home_page'))
    else:
        if request.method == 'POST': 
            cursor = conn.cursor()
            sql = f"""
                select * from user
                where email = %s
            """
            user_id = 0
            user_name = ""
            useremail = form.email.data
            try:
                cursor.execute(sql,useremail)
                data = cursor.fetchall()
                if data:
                    for row in data:
                        user_id = row[0]
                        user_name = row[2]
                else: 
                    flash(f'{useremail}: not found in our records, please register!', 'danger')
                    return redirect(url_for('login_page'))
            except Exception as e:
                print(e)
                print("Fail to load data!")
            token = get_reset_pass(1800, user_id)
            send_reset_email(token,useremail,user_name)
            flash('An email has been sent with instructions to reset your password.', category='success')
            return redirect(url_for('login_page'))
    return render_template('resetpassword.html', form = form)


@app.route("/resetpassword/<token>", methods=['GET', 'POST'])
def reset_pass(token):
    form = ResetPasswordForm()
    if 'loggedin' in session:
        return redirect(url_for('home_page'))
    else:
        user_id = verify_reset_pass(token)
        if user_id is None:
            flash('It is an invalid/expired token', category='danger')
            return redirect(url_for('resetpassword'))
        else:
            if form.validate_on_submit():
                if form.password.data == form.confirm_password.data:
                    # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                    newpassword = form.password.data
                    cursor = conn.cursor()
                    sql = f"""
                        UPDATE user set
                        password =%s
                        where user_id = %s
                    """
                    try:
                        cursor.execute(sql,(newpassword, user_id))
                        conn.commit()
                        flash('Your password has been updated! You can log in now', category='success')
                        return redirect(url_for('login_page'))
                    except Exception as e:
                        print(e)
                        conn.rollback()
                        print("Fail to update data!")
    return render_template('newpassword.html', form=form)

@app.route('/logout')
def logout():
   session.clear()
   flash(f"You've been logged out!", category='success')
   return redirect(url_for('login_page'))

def send_reset_email(token, email, name):
    msg = Message('Password Reset Request',
                  sender='istm6210ias@gmail.com',
                  recipients=[email])
    msg.body = f"""Hi {name},

    You have requested to reset your password. Here is your password reset link:

    {url_for('reset_pass', token=token, _external=True)}

    The link will expire in 30 minutes.
    
    If you didn't request an email to change your password, please contact us ASAP!
    
    \n @ Intelligent alert system
    """
    mail.send(msg)

def get_reset_pass(exp, id):
    s = Serializer(app.config['SECRET_KEY'], exp)
    return s.dumps({'user_id': id}).decode('utf-8')
    
def verify_reset_pass(token):
    cursor = conn.cursor()
    sql = f"""
        select * from user
        where user_id = %s
    """
    s = Serializer(app.config['SECRET_KEY'])
    try:
        id = 0
        user_id = s.loads(token)['user_id']
        try:
            cursor.execute(sql,user_id)
            data = cursor.fetchall()
            if data is not None:
                for row in data:
                    id = row[0]
        except Exception as e:
            print(e)
            print("Fail to load data!")
    except:
        return None
    return id

if __name__ == "__main__":
    app.run(debug=True,use_reloader=True)
    # app.config['TEMPLATES_AUTO_RELOAD'] = True
    # from livereload import Server
    # server = Server(app.wsgi_app)
    # server.serve(host = '0.0.0.0',port=5000)

    # from expression import gen,VideoCamera
    # gen(VideoCamera())
    
    # Process(target = app.run()).start()
    # Process(target = gen(VideoCamera)).start()
    
    # server = Server(app.wsgi_app)
    # # server.watch  
    # server.serve()