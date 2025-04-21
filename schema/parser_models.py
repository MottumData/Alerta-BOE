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
