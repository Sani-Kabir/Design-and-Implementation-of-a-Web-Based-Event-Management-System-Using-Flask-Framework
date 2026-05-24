from flask import Flask, render_template,redirect, request, jsonify
#from flask_mail import Mail, Message
import datetime, time, pymysql, threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time

app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_password'  # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

#mail = Mail(app)

# Dummy registered events (Later, we will fetch from the database)
registered_users = [
    {"name": "John Doe", "email": "john@example.com", "event": "Music Concert", "date": "2025-03-20"},
    {"name": "Jane Smith", "email": "jane@example.com", "event": "Tech Conference", "date": "2025-03-25"}
]
status = ""
reminder = False

def connect_db():
    connection = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        db="event_manager",
        cursorclass=pymysql.cursors.DictCursor
        )
    return connection.cursor(), connection

def send_alert(msg, subject, to):
    sender = "itguy.data@gmail.com"
    password = "tvedoijujkwkijua"
    body = f"{msg}"
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender,password)
            server.sendmail(sender,to,message.as_string())
        print("ok")
        return "ok"
    except:
        print("not sent")
        return "not sent"

def event_reminder():
    global reminder
    print("Reminder Script Started!")
    cursor,connection = connect_db()
    while True:
        time.sleep(1)
        sql = f"select * from reg_event where notify='false'"
        cursor.execute(sql)
        r_events = cursor.fetchall()
        if r_events is not None:
            for r_event in r_events:
                sql = f"select * from events where id='{r_event['event']}'"
                cursor.execute(sql)
                event = cursor.fetchone()

                target_date_str = str(event['date'])
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d")

                current_date = datetime.now()
                one_day_left = target_date - timedelta(days=1)

                if current_date.date() == one_day_left.date():
                    print("It's now 1 day left from the date you set")
                    subject = "Reminder: Your Event is Tomorrow!"
                    msg = f"""
Dear {r_event['fullname']},

This is a friendly reminder that the event you registered for {event['name']} is just 1 day away! 🎉

📍 Location: {event['location']}
📅 Date: {event['date']}
⏰ Time: {event['time_from']} to {event['time_to']}

We’re excited to have you join us! Please ensure you arrive on time and feel free to reach out if you have any questions.

See you soon!

Best regards,
Event Management System

"""
                    status = send_alert(msg, subject, r_event["email"])
                    if status == "ok":
                        sql = f"update reg_event set notify='true' where id='{r_event['id']}'"
                        cursor.execute(sql)
                        connection.commit()
                else:
                    #print("Not yet 1 day left") 
                    pass
            pass
        else:
            print("All event notified, Exited Loop")
            reminder = False
            break

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST","GET"])
def login():
    global status
    if request.method == "POST":
        cursor,connection = connect_db()
        email = request.form["email"]
        password = request.form["password"]
        sql = f"select * from users where email='{email}' and password='{password}'"
        cursor.execute(sql)
        user_data = cursor.fetchone()
        if user_data is not None:
            status = ""
            return redirect(f"/dashboard/{email}")
        status = "Wrong username/password"
        return redirect("/login")
    else:
        return render_template("login.html", status=status)

@app.route("/event-organizer/login", methods=["POST","GET"])
def event_organizer_login():
    global status
    if request.method == "POST":
        cursor,connection = connect_db()
        username = request.form["username"]
        password = request.form["password"]
        sql = f"select * from event_organizer where username='{username}' and password='{password}'"
        cursor.execute(sql)
        user_data = cursor.fetchone()
        if user_data is not None:
            status = ""
            return redirect(f"/event-organizer/dashboard/{username}")
        status = "Wrong username/password"
        return redirect("/event-organizer/login")
    else:
        return render_template("organizer-login.html", status=status)

@app.route("/register", methods=["POST","GET"])
def register():
    global status
    if request.method == "POST":
        cursor,connection = connect_db()
        fullname = request.form["fname"]
        email = request.form["email"]
        password = request.form["password"]
        sql = f"select * from users where email='{email}'"
        cursor.execute(sql)
        user_data = cursor.fetchone()
        if user_data is not None:
            status = "Username already exist!"
            return redirect("/login")
        else:
            status = ""
            sql = f"insert into users(email,fullname,password)values('{email}','{fullname}','{password}')"
            cursor.execute(sql)
            connection.commit()
            return redirect(f"/dashboard/{email}")
    else:
        return render_template("register.html", status=status)

@app.route("/event-organizer/dashboard/<string:username>", methods=["POST","GET"])
def event_organizer(username):
    cursor,connection = connect_db()
    sql = f"select * from events"
    cursor.execute(sql)
    events = cursor.fetchall()
    return render_template("organizer.html", username=username, events=events)

@app.route("/event-organizer/create-event/<string:username>", methods=["POST","GET"])
def create_event(username):
    if request.method == "POST":
        cursor,connection = connect_db()
        event_name = request.form["event_name"]
        date = request.form["date"]
        time_from = request.form["time-from"]
        time_to = request.form["time-to"]
        location = request.form["location"]
        image = request.form["image"]
        description = request.form["description"]
        sql = f"insert into events(name,date,time_from,time_to,location,image,description)values('{event_name}','{date}','{time_from}','{time_to}','{location}','{image}','{description}')"
        cursor.execute(sql)
        connection.commit()
        return redirect(f"/event-organizer/dashboard/{username}")
    
    return render_template("create_event.html", username=username)

@app.route("/event-organizer/edit-event/<string:username>/<int:id>", methods=["POST","GET"])
def edit_event(username,id):
    cursor,connection = connect_db()
    if request.method == "POST":
        event_name = request.form["event_name"]
        date = request.form["date"]
        time_from = request.form["time-from"]
        time_to = request.form["time-to"]
        location = request.form["location"]
        image = request.form["image"]
        description = request.form["description"]
        sql = f"update events set name='{event_name}',date='{date}',time_from='{time_from}',time_to='{time_to}',location='{location}',image='{image}',description='{description}' where id={id}"
        cursor.execute(sql)
        connection.commit()
        return redirect(f"/event-organizer/manage-events/{username}")
    sql = f"select * from events where id={id}"
    cursor.execute(sql)
    event = cursor.fetchone()
    return render_template("edit_event.html", username=username, event=event)

@app.route("/event-organizer/manage-events/<string:username>", methods=["POST","GET"])
def manage_event(username):
    cursor,connection = connect_db()
    if request.args.get('delid'):
        id = request.args.get('delid')
        sql = f"delete from events where id={id}"
        cursor.execute(sql)
        connection.commit()
        return redirect(f"/event-organizer/manage-events/{username}")
    sql = f"select * from events"
    cursor.execute(sql)
    events = cursor.fetchall()

    sql = f"select * from reg_event"
    cursor.execute(sql)
    reg_events = cursor.fetchall()
    no_of_reg_per_event = {}
    for event in events:
        no_of_reg_per_event[event['id']] = 0
        for reg_event in reg_events:
            if event["id"] == reg_event["id"]:
                no_of_reg_per_event[event['id']] += 1
    print(no_of_reg_per_event)   
    return render_template("manage_events.html", username=username, events=events, no_of_reg_per_event=no_of_reg_per_event)

@app.route("/event-organizer/profile/<string:username>", methods=["POST","GET"])
def profile(username):
    cursor,connection = connect_db()
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        email = request.form["email"]
        tel = request.form["phone"]
        bio = request.form["bio"]
        password = request.form["password"]
        sql = f"update event_organizer set name='{name}',email='{email}',tel='{tel}',bio='{bio}',password='{password}' where username='{username}'"
        cursor.execute(sql)
        connection.commit()
        return redirect(f"/event-organizer/dashboard/{username}")
    sql = f"select * from event_organizer where username='{username}'"
    cursor.execute(sql)
    user_data = cursor.fetchone()
    if user_data is not None:
        return render_template("profile.html", data=user_data)
    return redirect(f"/event-organizer/dashboard/{username}")

@app.route("/dashboard/<string:user>", methods=["GET"])
def dashboard(user):
    cursor,connection = connect_db()
    sql = f"select * from users where email='{user}'"
    cursor.execute(sql)
    user_data = cursor.fetchone()
    if user_data is not None:
        sql = f"select * from reg_event where email='{user}'"
        cursor.execute(sql)
        r_events = cursor.fetchall()
        reg_events = []
        for event in r_events:
            sql = f"select * from events where id='{event['event']}'"
            cursor.execute(sql)
            evt = cursor.fetchone()
            reg_events.append(evt)
        sql = f"select * from events"
        cursor.execute(sql)
        events = cursor.fetchall()
        notifications = []
        return render_template("dashboard.html", user=user, events=events, reg_events=reg_events, notifications=notifications)
    else:
        return redirect("/")

@app.route("/events", methods=["GET"])
def events():
    cursor,connection = connect_db()
    user = request.args.get("user")
    sql = f"select * from events"
    cursor.execute(sql)
    events = cursor.fetchall()
    return render_template("events.html", user=user, events=events)

@app.route("/register-event", methods=["POST","GET"])
def register_event():
    global status
    if request.method == "POST":
        cursor,connection = connect_db()
        fullname = request.form["fname"]
        email = request.form["email"]
        event_id = request.form["event"]
        event_time = request.form["time"]
        date = request.form["date"]
        
        sql = f"select * from event_list where id='{int(event_id)}'"
        cursor.execute(sql)
        event = cursor.fetchone()
        if event is not None:
            event = event['event']
            sql = f"insert into events(fullname,email,event,time,date)values('{fullname}','{email}','{event}','{event_time}','{date}')"
            cursor.execute(sql)
            connection.commit()
            status = "Event Registration Successful!"
            return redirect("/register-event")
    else:
        email = request.args.get("email")
        eventlist = []
        cursor,connection = connect_db()
        sql = f"select * from event_list"
        cursor.execute(sql)
        eventlist = cursor.fetchall()
        if eventlist is None:
            eventlist = []
        #print(eventlist)
        return render_template("event_registration.html",email=email, eventlist=eventlist, status=status)

@app.route("/view-event/<int:id>", methods=["POST", "GET"])
def view_event(id):
    global reminder
    cursor,connection = connect_db()
    if request.args.get("register_event"):
        _user = request.args.get("register_event")
        sql = f"select * from users where email='{_user}'"
        cursor.execute(sql)
        user_data = cursor.fetchone()
        if user_data is not None:
            name = user_data['fullname']
            sql = f"select * from reg_event where email='{_user}' and event={id}"
            cursor.execute(sql)
            event = cursor.fetchone()
            if event is None:
                sql = f"insert into reg_event(fullname,email,event)values('{name}','{_user}','{id}')"
                cursor.execute(sql)
                connection.commit()
                sql = f"select * from events where id={id}"
                cursor.execute(sql)
                event = cursor.fetchone()
                if reminder is False:
                    print("Starting Reminder")
                    threading.Thread(target=event_reminder).start()
                    reminder = True
                msg = f"Dear {name}, you successfully register to {event['name']} event which will take place at {event['location']} on {event['date']} from {event['time_from']} to {event['time_to']}\nWe will notifiy when is 1 day left to start the event. Thank you very much."
                status = send_alert(msg, "Event Notification", user_data["email"])
                return redirect(f"/view-event/{id}?user={_user}&statuscode=20022")
            else:
                return redirect(f"/view-event/{id}?user={_user}&statuscode=20021")
        else:
            return redirect(f"/view-event/{id}?user={_user}&statuscode=20023")
    
    statuscode = request.args.get("statuscode") if request.args.get("statuscode") else ""

    user = request.args.get("user") if request.args.get("user") else ""
    sql = f"select * from events where id={id}"
    cursor.execute(sql)
    event = cursor.fetchone()
    print(statuscode)
    if statuscode == "20021":
        statuscode = "Your already registered to this event."
    elif statuscode == "20022":
        statuscode = "You have registered to this event successfully"
    elif statuscode == "20023":
        statuscode = "Sign up first in order to register to any of our events!"
    else:
        print("NONE")
        statuscode = ""
    
    return render_template("event_details.html",user=user, statuscode=statuscode, event=event)

@app.route('/send_reminders', methods=['GET'])
def send_reminders():
    today = datetime.date.today()
    for user in registered_users:
        event_date = datetime.datetime.strptime(user['date'], "%Y-%m-%d").date()
        days_left = (event_date - today).days
        
        if days_left == 1:  # Send reminder 1 day before the event
            subject = f"Reminder: {user['event']} is happening tomorrow!"
            body = f"Hello {user['name']},\n\nThis is a reminder that you have registered for {user['event']} happening on {user['date']}.\n\nBest Regards,\nEvent Management Team"
            
            #msg = Message(subject, recipients=[user['email']], body=body)
            #mail.send(msg)
    
    return jsonify({"message": "Reminders sent successfully!"})



if __name__ == '__main__':
    app.run(debug=True)


@app.route('/send-test-email')
def send_test_email():
    #msg = Message('Hello from Flask!', recipients=['recipient@example.com'])  # Replace with recipient's email
    #msg.body = 'This is a test email sent from Flask-Mail.'
    #mail.send(msg)
    return "Test email sent!"
