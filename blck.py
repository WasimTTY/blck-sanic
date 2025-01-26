import os
import time
import asyncio
import magic
from aiologger.loggers.json import JsonLogger
from aiologger.handlers.files import AsyncFileHandler
from sanic import Sanic, Blueprint
from sanic.response import json, html, file
from jinja2 import Environment, FileSystemLoader
from random import choice
from string import ascii_uppercase, ascii_lowercase
import argparse
from datetime import datetime

parser = argparse.ArgumentParser(description="Sanic application with file upload and expiration handling.")
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')

args = parser.parse_args()

project_dir = os.getcwd()
log_file_path = os.path.join(project_dir, 'blck.log')

logger = JsonLogger.with_default_handlers(level='DEBUG' if args.debug else 'INFO', flatten=True)
handler = AsyncFileHandler(log_file_path)
logger.add_handler(handler)

app = Sanic(__name__)
bp = Blueprint('blck', url_prefix='/')
files_dir = 'files'
os.makedirs(files_dir, exist_ok=True)

bp.static('/files', files_dir)
jinja_env = Environment(loader=FileSystemLoader('templates'))

file_metadata = {}
EXPIRATION_TIME = 4 * 60 * 60
app.config.PROXIES_COUNT = 1

def get_current_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@bp.route("/health")
async def health_check(request):
    current_time = get_current_time()
    await logger.debug(f"Health check route accessed at {current_time} with the method: {request.method}")
    return json({'status': 'healthy'})

@bp.route("/", methods=['GET', 'POST'])
async def index(request):
    current_time = get_current_time()
    await logger.debug(f"Index route accessed at {current_time} with the method: {request.method}")
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
    base_url = f"{scheme}://{request.host}/"
    if request.method == 'GET':
        return html(jinja_env.get_template('index.html').render(r=request.app.config.get("SERVER_URL", base_url)))
    return await handle_file_upload(request, base_url)

@bp.route("/<urlshort>")
async def urlget(request, urlshort):
    current_time = get_current_time()
    await logger.debug(f"Request received for URL short: {urlshort} at {current_time}")
    file_path = next((os.path.join(files_dir, f) for f in os.listdir(files_dir) if f.startswith(urlshort)), None)
    if not file_path or not os.path.isfile(file_path):
        return json({'error': 'File not found'})

    file_metadata[urlshort]['last_accessed'] = time.time()
    mime = magic.from_file(file_path, mime=True)
    try:
        response = await file(file_path, mime_type=mime)
        os.remove(file_path)
        return response
    except Exception as e:
        await logger.error(f"Error serving file: {e} at {current_time}")
        return json({'error': 'Error serving file'})

async def handle_file_upload(request, base_url):
    current_time = get_current_time()
    await logger.debug(f"Handling file upload at {current_time} with the method: {request.method}")
    if not request.files or 'c' not in request.files:
        return json({'error': 'No file provided'})

    file_urls = []
    for file in request.files['c']:
        await logger.debug(f"Processing file: {file.name} with size: {len(file.body)} bytes at {current_time}")
        file_id = ''.join(choice(ascii_uppercase + ascii_lowercase) for _ in range(6))
        file_path = os.path.join(files_dir, file_id)

        with open(file_path, 'wb') as f:
            f.write(file.body)

        mime_type = file.type or magic.from_file(file_path, mime=True)
        if mime_type:
            os.rename(file_path, f"{file_path}.{mime_type.split('/')[1]}")
            await logger.debug(f"File renamed to: {file_path}.{mime_type.split('/')[1]} at {current_time}")

        file_metadata[file_id] = {'last_accessed': time.time()}
        file_url = f"{base_url}{file_id}"
        file_urls.append({'url': file_url, 'name': file.name})

    return json({'files': file_urls})

async def clean_up_expired_files():
    while True:
        current_time = get_current_time()
        await logger.debug(f"Running cleanup tasks for expired files at {current_time}.")
        current_time = time.time()
        for file_id, metadata in list(file_metadata.items()):
            last_accessed = metadata['last_accessed']
            if current_time - last_accessed > EXPIRATION_TIME:
                file_path = os.path.join(files_dir, file_id)
                if os.path.exists(file_path):
                    await logger.debug(f"Expired file {file_id} deleted: {file_path} at {current_time}")
                    os.remove(file_path)
                del file_metadata[file_id]

        await asyncio.sleep(60)

@bp.listener('before_server_start')
async def before_server_start(app, loop):
    current_time = get_current_time()
    await logger.debug(f"Adding cleanup task at {current_time}.")
    app.add_task(clean_up_expired_files())
    await logger.debug(f"Starting sanic application at {current_time}")

app.blueprint(bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=args.debug)
