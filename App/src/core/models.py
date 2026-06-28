from pydantic import BaseModel
from typing import List, Optional

class Element(BaseModel):
    id: str
    type: str
    x: int
    y: int
    width: int
    height: int
    layer_index: int
    is_visible: bool = True

class Slide(BaseModel):
    id: str
    background_color: str = "#ffffff"
    elements: List[Element] = []

class Presentation(BaseModel):
    id: str
    title: str = "Nova Apresentação"
    resolution: str = "1920x1080"
    slides: List[Slide] = []
