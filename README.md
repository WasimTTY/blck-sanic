# blck-sanic

An ephemeral pastebin. you can only retrieve the paste once, and then it is deleted from the server.

## Credits

This project is a refactor of the original [blck](https://github.com/parazyd/blck) repository, developed by [parazyd](https://github.com/parazyd). The original repository was built using Flask, and this version has been adapted to use Sanic for better async capabilities.

> **Note:**  The core functionality and features have been preserved.

## Added Features
- **Async Logging**: Integrated [aiologger](https://async-worker.github.io/aiologger/) for asynchronous logging.
- **File Expiration**: Files automatically expire after 4 hours, and expired files are cleaned up periodically.


## Installation

use `pyproject.toml` to define project metadata and dependencies or just run `uv init`

refer  the astral-uv documentation: https://docs.astral.sh/uv/ 

run `uv run blck.py -d` to the run the application in debug mode 

nginx
-----

```
location / {
	proxy_set_header Host $host;
	proxy_set_header X-Real-IP $remote_addr;
	proxy_set_header X-Forwarded-Proto https;
	proxy_pass http://127.0.0.1:8000;
}
```


## Usage

either use the website, or curl:

```
curl -F 'c=@-' http://whatever.domain < file
```
