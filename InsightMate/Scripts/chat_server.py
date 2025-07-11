import os
from flask import Flask
from dotenv import load_dotenv



load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

register_common(app)


@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
