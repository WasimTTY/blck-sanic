import os
import logging
import magic
import time
import asyncio
from sanic import Sanic, Blueprint
from sanic.response import json, html, file
from jinja2 import Environment, FileSystemLoader
from random import choice
from string import ascii_uppercase, ascii_lowercase

app = Sanic(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler(), logging.FileHandler('app.log', mode='a')])
logger = logging.getLogger('sanic')

bp = Blueprint('blck', url_prefix='/')
files_dir = 'files'
os.makedirs(files_dir, exist_ok=True)
logger.debug(f"Ensured that the '{files_dir}' directory exists.")

bp.static('/files', files_dir)

jinja_env = Environment(loader=FileSystemLoader('templates'))

file_metadata = {}
EXPIRATION_TIME = 4 * 60 * 60

@bp.route("/health")
async def health_check(request):
    return json({'status': 'healthy'})

@bp.route("/", methods=['GET', 'POST'])
async def index(request):
    if request.method == 'GET':
        return html(jinja_env.get_template('index.html').render(r=request.app.config.get("SERVER_URL", f"http://{request.host}/")))
    return await handle_file_upload(request)

@bp.route("/<urlshort>")
async def urlget(request, urlshort):
    file_path = next((os.path.join(files_dir, f) for f in os.listdir(files_dir) if f.startswith(urlshort)), None)
    if not file_path or not os.path.isfile(file_path):
        return json({'error': 'File not found'}, status=404)

    file_metadata[urlshort]['last_accessed'] = time.time()

    mime = magic.from_file(file_path, mime=True)
    try:
        response = await file(file_path, mime_type=mime)
        os.remove(file_path)
        return response
    except Exception as e:
        return json({'error': 'Error serving file'}, status=500)

async def handle_file_upload(request):
    if not request.files or 'c' not in request.files:
        return json({'error': 'No file provided'}, status=400)

    file_urls = []
    for file in request.files['c']:
        file_id = ''.join(choice(ascii_uppercase + ascii_lowercase) for _ in range(6))
        file_path = os.path.join(files_dir, file_id)
        
        with open(file_path, 'wb') as f:
            f.write(file.body)

        mime_type = file.type or magic.from_file(file_path, mime=True)
        if mime_type:
            os.rename(file_path, f"{file_path}.{mime_type.split('/')[1]}")

        file_metadata[file_id] = {'last_accessed': time.time()}

        # Generate the URL for the uploaded file
        file_url = f'{request.app.config.get("SERVER_URL", f"http://{request.host}/")}{file_id}'
        file_urls.append({'url': file_url, 'name': file.name})
    
    return json({'files': file_urls})

async def clean_up_expired_files():
    while True:
        current_time = time.time()
        for file_id, metadata in list(file_metadata.items()):
            last_accessed = metadata['last_accessed']
            
            if current_time - last_accessed > EXPIRATION_TIME:
                file_path = os.path.join(files_dir, file_id)
                if os.path.exists(file_path):
                    os.remove(file_path)
                del file_metadata[file_id]
        
        await asyncio.sleep(60)

@bp.listener('before_server_start')
async def before_server_start(app, loop):
    app.add_task(clean_up_expired_files())

app.blueprint(bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
