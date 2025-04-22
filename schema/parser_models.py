from typing import List
from pydantic import BaseModel, Field

class BiodiversitySummaryParser(BaseModel):
    Biodiversidad: str = Field(
        description='"Sí" si el texto menciona biodiversidad; "No" en caso contrario',
        pattern=r"^(Sí|No)$"
    )
    Resumen: str = Field(
        description="Un resumen breve (1 párrafo) del contenido del documento"
    )

class BOEEntryClassification(BaseModel):
    identificador: str = Field(..., description="Identificador del BOE")
    relacionado_con_biodiversidad: str = Field(
        ...,
        description='"Sí" o "No"',
        pattern=r"^(Sí|No)$"
    )

class BOEClassificationResponse(BaseModel):
    resultados: List[BOEEntryClassification]