from typing import Dict, Type
from .pain_001 import Pain001Parser
from .camt_054 import Camt054Parser
from .camt_054_generator import Camt054Generator
from .pain_001_generator import Pain001Generator
from .base_interfaces import BaseParser, BaseGenerator # Import from new file

# Registry for input parsers
parser_registry: Dict[str, Type[BaseParser]] = {
    "PAIN.001": Pain001Parser,
    "CAMT.054": Camt054Parser,
}

# Registry for output generators
generator_registry: Dict[str, Type[BaseGenerator]] = {
    "PAIN.001": Pain001Generator, # For when PAIN.001 is the desired output format
    "CAMT.054": Camt054Generator, # For when CAMT.054 is the desired output format
}