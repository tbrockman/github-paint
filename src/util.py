from enum import Enum
from dataclasses import dataclass

class Color(Enum):
    GREY = 0
    LIGHT_GREEN = 1
    GREEN = 2
    DARK_GREEN = 3
    DARKEST_GREEN = 4

@dataclass
class Pixel:
    color: Color
    
    def __repr__(self):
        return '█' if self.color != Color.GREY else ' '