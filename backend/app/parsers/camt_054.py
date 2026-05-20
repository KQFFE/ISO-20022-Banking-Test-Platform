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
            val_date_node = ntry.find('.//ns:ValDt/ns:Dt', self.ns)
            cdt_dbt_ind_node = ntry.find('ns:CdtDbtInd', self.ns)
            
            # Additional fields for richer output
            acct_svcr_ref_node = ntry.find('ns:AcctSvcrRef', self.ns)
            accptnc_dt_tm_node = ntry.find('.//ns:RltdDts/ns:AccptncDtTm', self.ns)

            # Bank Transaction Code details
            bk_tx_domn_cd_node = ntry.find('.//ns:BkTxCd/ns:Domn/ns:Cd', self.ns)
            bk_tx_fmly_cd_node = ntry.find('.//ns:BkTxCd/ns:Domn/ns:Fmly/ns:Cd', self.ns)
            bk_tx_subfmly_cd_node = ntry.find('.//ns:BkTxCd/ns:Domn/ns:Fmly/ns:SubFmlyCd', self.ns)

            # Debtor Information
            dbtr_nm_node = ntry.find('.//ns:Dbtr/ns:Nm', self.ns)
            dbtr_addr_ctry_node = ntry.find('.//ns:Dbtr/ns:PstlAdr/ns:Ctry', self.ns)
            dbtr_addr_lines = [line.text for line in ntry.findall('.//ns:Dbtr/ns:PstlAdr/ns:AdrLine', self.ns) if line.text]

            # Remittance Information (handle multiple unstructured and structured)
            remittance_info = {}
            ustrd_rmts = [ustrd.text for ustrd in ntry.findall('.//ns:RmtInf/ns:Ustrd', self.ns) if ustrd.text]
            if ustrd_rmts:
                remittance_info['unstructured'] = ustrd_rmts
            strd_cdtr_ref_node = ntry.find('.//ns:RmtInf/ns:Strd/ns:CdtrRefInf/ns:Ref', self.ns)
            if strd_cdtr_ref_node is not None:
                remittance_info['structured'] = {'CdtrRefInf': strd_cdtr_ref_node.text}
            
            if amt_node is not None:
                transactions.append({
                    "instruction_id": ntry.find('ns:NtryRef', self.ns).text if ntry.find('ns:NtryRef', self.ns) is not None else "N/A",
                    "end_to_end_id": e2e_node.text if e2e_node is not None else None,
                    "amount": float(amt_node.text) if amt_node.text else 0.0,
                    "currency": amt_node.attrib.get('Ccy'),
                    "status": "Pending",
                    "bic": bic,
                    "iban": iban,
                    "date": date_node.text if date_node is not None else None, # Booking Date
                    "value_date": val_date_node.text if val_date_node is not None else None,
                    "credit_debit_indicator": cdt_dbt_ind_node.text if cdt_dbt_ind_node is not None else "CRDT", # Default to CRDT for CAMT.054
                    "debtor_name": dbtr_nm_node.text if dbtr_nm_node is not None else "Unknown",
                    "debtor_address_country": dbtr_addr_ctry_node.text if dbtr_addr_ctry_node is not None else None,
                    "debtor_address_lines": dbtr_addr_lines,
                    "remittance_info": remittance_info if remittance_info else None, # Store as dict
                    "acct_svcr_ref": acct_svcr_ref_node.text if acct_svcr_ref_node is not None else None,
                    "bank_transaction_code_domain": bk_tx_domn_cd_node.text if bk_tx_domn_cd_node is not None else None,
                    "bank_transaction_code_family": bk_tx_fmly_cd_node.text if bk_tx_fmly_cd_node is not None else None,
                    "bank_transaction_code_subfamily": bk_tx_subfmly_cd_node.text if bk_tx_subfmly_cd_node is not None else None,
                    "acceptance_date_time": accptnc_dt_tm_node.text if accptnc_dt_tm_node is not None else None,
                })
        return transactions