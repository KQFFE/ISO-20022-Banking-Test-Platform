from typing import Dict, Type

# Define a base interface for parsers
class BaseParser:
    def __init__(self, xml_content: bytes):
        raise NotImplementedError("Subclasses must implement __init__")
    def get_transactions(self) -> list:
        raise NotImplementedError("Subclasses must implement get_transactions")

# Define a base interface for generators
class BaseGenerator:
    def generate_xml(self, tx_data: dict, flow_data: dict) -> str:
        raise NotImplementedError("Subclasses must implement generate_xml")