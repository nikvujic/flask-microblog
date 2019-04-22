# Flask-microblog

A simple microblog powered by Flask. Users can create accounts and create posts other users can see. Every user can view basic info of any other user and edit their own. Users can also create, update and delete their posts. App also features password recovery system that sends a password reset link (which expires in 30minutes) to their registered email.

## Setup

To run the app you must have Python 3.6 or higher installed. After cloning the repo, it is recommended to use a virtual environment. All the modules needed to run the app are listen in requirements.txt file. To install the modules make sure you are using Python 3 and run:

```
pip install -r requirements.txt
```

After that you can run the app from run.py file:

```
python run.py
```

## Info on some modules

* The Pillow module is used to resize images that users submit.
* The flask-mail module is used to send password recovery emails to the user.
* The flask_bcrypt module is used to hash the passwords before storing them.
* The itsdangerous module is used for the reset token sent to user's email.

## Notes

Before any kind of deployment you should edit app.config['SECRET_KEY'] variable. Also, edit the MAIL_USERNAME and MAIL_PASSWORD values to match your own (they should be stored in some other local file and imported to the project, but I'm too lazy to configure it).
