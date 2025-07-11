import os
from flask import Flask
from dotenv import load_dotenv

from server_common import register_common, WEB_DIR

app = Flask(__name__, static_folder=WEB_DIR, static_url_path='')

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

register_common(app)

if __name__ == '__main__':
    app.run(port=5000)
