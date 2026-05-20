import xml.etree.ElementTree as ET
from .base_interfaces import BaseParser

class Camt054Parser(BaseParser):
    """Parses ISO 20022 Camt.054 Bank-to-Customer Debit/Credit Notification."""
    
    def __init__(self, xml_content: bytes):
        self.root = ET.fromstring(xml_content)
        if isinstance(self.root.tag, str) and self.root.tag.startswith('{'):
            self.namespace = self.root.tag.split('}')[0].strip('{')
        else:
            self.namespace = 'urn:iso:std:iso:20022:tech:xsd:camt.054.001.02'
        
        self.ns = {'ns': self.namespace}

    def get_transactions(self):
        transactions = []
        # Extract Account Info (IBAN/BIC) from the Notification level
        iban_node = self.root.find('.//ns:Acct/ns:Id/ns:IBAN', self.ns)
        bic_node = self.root.find('.//ns:Acct/ns:Svcr/ns:FinInstnId/ns:BIC', self.ns)
        
        iban = iban_node.text if iban_node is not None else None
        bic = bic_node.text if bic_node is not None else None

        # Find all Entry (Ntry) blocks
        entries = self.root.findall('.//ns:Ntry', self.ns)
        
        for ntry in entries:
            amt_node = ntry.find('ns:Amt', self.ns)
            e2e_node = ntry.find('.//ns:EndToEndId', self.ns)
            date_node = ntry.find('.//ns:BookgDt/ns:Dt', self.ns)
            cdtr_nm_node = ntry.find('.//ns:Dbtr/ns:Nm', self.ns) # In CRDT, Dbtr is the "payer"
            
            if amt_node is not None:
                transactions.append({
                    "instruction_id": ntry.find('ns:NtryRef', self.ns).text if ntry.find('ns:NtryRef', self.ns) is not None else "N/A",
                    "end_to_end_id": e2e_node.text if e2e_node is not None else None,
                    "amount": float(amt_node.text) if amt_node.text else 0.0,
                    "currency": amt_node.attrib.get('Ccy'),
                    "status": "Pending",
                    "bic": bic,
                    "iban": iban,
                    "date": date_node.text if date_node is not None else None,
                    "creditor_name": cdtr_nm_node.text if cdtr_nm_node is not None else "Unknown",
                })
        return transactions