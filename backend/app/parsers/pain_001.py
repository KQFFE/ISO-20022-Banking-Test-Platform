import xml.etree.ElementTree as ET
from .base_interfaces import BaseParser # Import BaseParser from new file

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
            # Common info for all transactions in this PmtInf block
            bic_node = pmt.find('.//ns:DbtrAgt/ns:FinInstnId/ns:BIC', self.ns)
            iban_node = pmt.find('.//ns:DbtrAcct/ns:Id/ns:IBAN', self.ns)
            date_node = pmt.find('ns:ReqdExctnDt', self.ns)
            
            bic = bic_node.text if bic_node is not None else None
            iban = iban_node.text if iban_node is not None else None
            execution_date = date_node.text if date_node is not None else None

            # Iterate through individual transactions
            tx_infos = pmt.findall('ns:CdtTrfTxInf', self.ns)
            for tx in tx_infos:
                instr_id_node = tx.find('ns:PmtId/ns:InstrId', self.ns)
                e2e_id_node = tx.find('ns:PmtId/ns:EndToEndId', self.ns)
                amt_node = tx.find('ns:Amt/ns:InstdAmt', self.ns)
                cdtr_nm_node = tx.find('ns:Cdtr/ns:Nm', self.ns)
                # Extract Remittance Info (Unstructured or Structured)
                ustrd_node = tx.find('.//ns:RmtInf/ns:Ustrd', self.ns)
                strd_node = tx.find('.//ns:RmtInf/ns:Strd/ns:RfrdDocInf/ns:Nb', self.ns)
                
                if amt_node is not None:
                    amount = amt_node.text
                    transactions.append({
                        "instruction_id": instr_id_node.text if instr_id_node is not None else "NOT_PROVIDED",
                        "end_to_end_id": e2e_id_node.text if e2e_id_node is not None else None,
                        "amount": float(amount) if amount else 0.0,
                        "currency": amt_node.attrib.get('Ccy'),
                        "status": "Pending",
                        "bic": bic,
                        "iban": iban,
                        "date": execution_date,
                        "creditor_name": cdtr_nm_node.text if cdtr_nm_node is not None else "Unknown",
                        "remittance_info": ustrd_node.text if ustrd_node is not None else (strd_node.text if strd_node is not None else None)
                    })
        return transactions
