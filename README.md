<h1>Custom Recipes</h1>
<p>
    Designed by Alexandr Timoshenko specifically for Digital Ecosystems as a test task for employment.
</p>
<h3>Technologies Stack</h3>
<ul>
    <li>Python 3</li>
    <li>Postgresql 10</li>
    <li>virtualenv</li>
    <li>aiohttp</li>
    <li>aiohttp-cors</li>
    <li>aiohttp-security</li>
    <li>aiohttp-session</li>
    <li>Tortoise ORM</li>
</ul>

<h3>Optional</h3>
<ul>
    <li>uvloop</li>
</ul>

# server
```
cd custom_recipes
```

### Create venv
##### Windows:
```
python -m venv venv
cd venv/Scripts
activate.bat
cd ../../
```
##### Linux:
```
python3 -m venv venv
source venv/bin/activate
```

### Install requirements
##### Windows:
```
pip install -r requirements.txt
```
##### Linux:
```
pip3 install -r requirements.txt
```
###### Linux Optional:
```
pip3 install uvloop
```

### Customize configuration in config.json!

### Run server
##### Windows:
```
python main.py
```
##### Linux:
```
python3 main.py
```