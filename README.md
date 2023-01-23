# Yatube

Online service for post publication with ability to comment them. Available new user registration, password changing (by email sent link), image appending. Implemented pagination and caching.

### How to run application

- Clone repo:

```git clone https://github.com/AlexanderUp/hw05_final.git```

- Create and activate virtual environment:

```python3 -m pip venv venv```
```source venv/bin/activate```

- Change directory to hw05_final and install requirements:

```cd hw05_final```
```python3 -m pip install -r requirements.txt```

- Change directory to yatube and make and apply migrations:

```cd yatube```
```python3 manage.py makemigrations```
```python3 manage.py migrate```

- Create superuser:

```python3 manage.py createsuperuser```

- Change directory to yatube and run server:

```cd yatube```
```python3 manage.py runserver```

- Application is available on:

```127.0.0.1:8000```
