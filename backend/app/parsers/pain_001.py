import xml.etree.ElementTree as ET

class Pain001Parser:
    """Parses ISO 20022 Pain.001 Credit Transfer Initiation."""
    
    def __init__(self, xml_content: bytes):
        # Using bytes allows the XML parser to handle encoding declarations automatically
        self.root = ET.fromstring(xml_content)
        # Extract namespace dynamically from the root tag
        if isinstance(self.root.tag, str) and self.root.tag.startswith('{'):
            self.namespace = self.root.tag.split('}')[0].strip('{')
        else:
            self.namespace = 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03'
        
        self.ns = {'ns': self.namespace}

    def get_transactions(self):
        transactions = []
        # Find all Payment Information blocks
        pmt_infos = self.root.findall('.//ns:PmtInf', self.ns)
        
        for pmt in pmt_infos:
            # Use safe finding to prevent AttributeErrors if elements are missing
            pmt_id_node = pmt.find('.//ns:PmtId/ns:InstrId', self.ns)
            amt_node = pmt.find('.//ns:InstdAmt', self.ns)
            bic_node = pmt.find('.//ns:DbtrAgt/ns:FinInstnId/ns:BIC', self.ns)
            iban_node = pmt.find('.//ns:DbtrAcct/ns:Id/ns:IBAN', self.ns)
            
            if amt_node is not None:
                instr_id = pmt_id_node.text if pmt_id_node is not None else "NOT_PROVIDED"
                amount = amt_node.text
                currency = amt_node.attrib.get('Ccy')
                bic = bic_node.text if bic_node is not None else None
                iban = iban_node.text if iban_node is not None else None
                
                transactions.append({
                    "instruction_id": instr_id,
                    "amount": float(amount) if amount else 0.0,
                    "currency": currency,
                    "status": "Pending",
                    "bic": bic,
                    "iban": iban
                })
        return transactions
