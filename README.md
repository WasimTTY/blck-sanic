# blck-sanic

An ephemeral pastebin. you can only retrieve the paste once, and then it is deleted from the server.

## Credits

This project is a refactor of the original [blck](https://github.com/parazyd/blck) repository, developed by [parazyd](https://github.com/parazyd). The original repository was built using Flask, and this version has been adapted to use Sanic for better async capabilities.

> **Note:**  The core functionality and features have been preserved.


## Installation

use `pyproject.toml` to define project metadata and dependencies or just run `uv init`

refer  the astral-uv documentation: https://docs.astral.sh/uv/ 

run `uv run blck.py -d` to the run the application in debug mode 



## Usage

either use the website, or curl:

```
curl -F 'c=@-' http://whatever.domain < file
```
