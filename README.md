# HospiHelp

Flask website (doctors, hospitals, appointments, blood finder).

## Before you upload
Copy your own HTML files into `templates/` and your CSS/JS/images into `static/`.
Required templates: index, specialists, hospitals, doctor, appointment,
my_appointments, blood_finder, login, signup, profile, menu (all .html).

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000/

## Environment variables
- `SECRET_KEY`    : long random string (required in production)
- `DATABASE_PATH` : optional, full path of the SQLite file

## Start command (Render, Railway, Heroku, VPS)
```
gunicorn app:app
```

## PythonAnywhere
Upload the folder, create a virtualenv, `pip install -r requirements.txt`,
then in the Web tab set the WSGI file to import `application` from `wsgi.py`
and set the SECRET_KEY in the WSGI file: `os.environ["SECRET_KEY"] = "..."`.

## Note on data
SQLite stores accounts/appointments in a file. Hosts with temporary disks
(Render free, Heroku, Vercel) lose that file on restart.
PythonAnywhere or a VPS keep it permanently.
