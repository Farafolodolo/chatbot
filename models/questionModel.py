from typing import List
from pydantic import BaseModel, Field

class QAItem(BaseModel):
    pregunta: str = Field(..., example="¿Cómo simplifico la fracción 8/12?")
    respuesta: str = Field(..., example="Divide numerador y denominador por su MCD (4): obtienes 2/3.")
    tags: List[str] = Field(default_factory=list, example=["simplificar", "fracciones", "8/12"])

class QADocument(BaseModel):
    tema: str = Field(..., example="mate")
    subtema: str = Field(..., example="fracciones")
    qas: List[QAItem]