from __future__ import annotations

import os
from airflow.models.baseoperator import BaseOperator


class WordCountOperator(BaseOperator):
    """
    Operador personalizado que cuenta palabras de un archivo de texto.

    - Lee el archivo dado por `filepath`
    - Retorna el total de palabras (queda disponible como XCom)
    - `filepath` es templatable (puedes usar {{ ds }}, etc.)
    """
    template_fields = ("filepath",)

    def __init__(self, *, filepath: str, **kwargs):
        super().__init__(**kwargs)
        self.filepath = filepath

    def execute(self, context):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"No existe el archivo: {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8") as f:
            text = f.read()

        count = len(text.split())
        self.log.info("Conteo de palabras en %s = %s", self.filepath, count)
        return count
