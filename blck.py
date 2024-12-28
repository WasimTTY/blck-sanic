import os
import logging
import magic
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
app.static('/files', files_dir)
jinja_env = Environment(loader=FileSystemLoader('templates'))

@bp.route("/health")
async def health_check(request):
    logger.debug("Health check route accessed.")
    return json({'status': 'healthy'})

@bp.route("/", methods=['GET', 'POST'])
async def index(request):
    logger.debug(f"Index route accessed with method {request.method}.")
    if request.method == 'GET':
        logger.debug("Rendering index page.")
        return html(jinja_env.get_template('index.html').render(r=request.app.config.get("SERVER_URL", f"http://{request.host}/")))
    return await handle_file_upload(request)

@bp.route("/<urlshort>")
async def urlget(request, urlshort):
    logger.debug(f"Fetching file for URL short: {urlshort}.")
    file_path = next((os.path.join(files_dir, f) for f in os.listdir(files_dir) if f.startswith(urlshort)), None)
    if not file_path or not os.path.isfile(file_path):
        logger.error(f"File {urlshort} not found.")
        return json({'error': 'File not found'}, status=404)
    mime = magic.from_file(file_path, mime=True)
    logger.debug(f"Detected MIME type for {urlshort}: {mime}.")
    try:
        response = await file(file_path, mime_type=mime)
        os.remove(file_path)
        logger.debug(f"File {urlshort} served and deleted.")
        return response
    except Exception as e:
        logger.error(f"Error serving file {urlshort}: {e}")
        return json({'error': 'Error serving file'}, status=500)

async def handle_file_upload(request):
    logger.debug("Handling file upload.")
    if not request.files or 'c' not in request.files:
        logger.error("No file uploaded.")
        return json({'error': 'No file provided'}, status=400)
    file = request.files['c'][0]
    file_id = ''.join(choice(ascii_uppercase + ascii_lowercase) for _ in range(6))
    logger.debug(f"Generated file ID: {file_id}.")
    file_path = os.path.join(files_dir, file_id)
    with open(file_path, 'wb') as f:
        f.write(file.body)
    logger.debug(f"File saved to {file_path}.")
    mime_type = file.type or magic.from_file(file_path, mime=True)
    if mime_type:
        os.rename(file_path, f"{file_path}.{mime_type.split('/')[1]}")
        logger.debug(f"Renamed file to include MIME extension: {mime_type.split('/')[1]}.")
    return json({'url': f'{request.app.config.get("SERVER_URL", f"http://{request.host}/")}{file_id}'})

app.blueprint(bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
