from shiny.express import wrap_express_app
from pathlib import Path


def create_app():
    return wrap_express_app((Path(__file__).parent / "app.py").resolve())

app = create_app()