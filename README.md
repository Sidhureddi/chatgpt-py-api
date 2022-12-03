# ChatGPT api

* It uses playwright and chromium to open browser and parse html.
* It is an unoffical api for development purpose only.


# How to install

* Make sure that python and virual environment is installed.

* Create a new virtual environment

```python
# one time
virtualenv -p $(which python3) pyenv

# everytime you want to run the server
source pyenv/bin/activae
```

* Now install the dependencies from `requirements.txt`

```
python requirements.txt
```

* If you are installing playwright for the first time, it will ask you to run this command for one time only.

```
playwright install
```

* Now run the server

```
python server.py
```

# Credit

### Thanks to 
- [Daniel Gross](https://github.com/danielgross/whatsapp-gpt). He initially built this as a whatsapp bot that interacts with chatGPT.
- [Taranjeet](https://github.com/taranjeet/chatgpt-api): He took the script as an individual file and added documentation for how to install and run it with python.
