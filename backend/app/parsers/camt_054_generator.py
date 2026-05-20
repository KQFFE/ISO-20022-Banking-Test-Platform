import xml.sax.saxutils as saxutils
from datetime import datetime
from .base_interfaces import BaseGenerator # Import BaseGenerator

class Camt054Generator(BaseGenerator):
    """Generates CAMT.054 Bank-to-Customer Debit/Credit Notification XML."""

    def generate_xml(self, tx_data: dict, flow_data: dict) -> str:
        tx = tx_data['transaction']
        raw_data_content = tx_data['raw_data_content']
        transactions_list = tx_data['transactions_list']
        batch_total = tx_data['batch_total']
        batch_count = tx_data['batch_count']

        cre_dt_tm = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        ns = "urn:iso:std:iso:20022:tech:xsd:camt.054.001.02"
        root_tag = "BkToCstmrDbtCdtNtfctn"

        xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="{ns}">\n    <{root_tag}>\n'

        xml_content += (
            f'        <GrpHdr>\n'
            f'            <MsgId>NOTIF-{tx.instruction_id}</MsgId>\n'
            f'            <CreDtTm>{cre_dt_tm}</CreDtTm>\n'
            f'        </GrpHdr>\n'
            f'        <Ntfctn>\n'
            f'            <Id>NTF-{tx.id}</Id>\n'
            f'            <CreDtTm>{cre_dt_tm}</CreDtTm>\n'
            f'            <TxsSummry>\n'
            f'                <TtlNtries>\n'
            f'                    <NbOfNtries>{batch_count}</NbOfNtries>\n'
            f'                    <Sum>{float(batch_total):.2f}</Sum>\n'
            f'                    <CdtDbtInd>DBIT</CdtDbtInd>\n'
            f'                </TtlNtries>\n'
            f'            </TxsSummry>\n'
        )
        items = transactions_list if transactions_list else [{"amount": tx.amount, "currency": tx.currency, "instruction_id": tx.instruction_id}]
        for item in items:
            amt = float(item.get("amount", 0))
            ccy = saxutils.escape(str(item.get("currency", tx.currency)))
            e2e = saxutils.escape(str(item.get("end_to_end_id") or item.get("instruction_id") or tx.instruction_id))
            
            xml_content += (
                f'            <Ntry>\n'
                f'                <Amt Ccy="{ccy}">{amt:.2f}</Amt>\n'
                f'                <CdtDbtInd>DBIT</CdtDbtInd>\n'
                f'                <Sts>BOOK</Sts>\n'
                f'                <NtryDtls>\n'
                f'                    <TxDtls>\n'
                f'                        <Refs>\n'
                f'                            <EndToEndId>{e2e}</EndToEndId>\n'
                f'                        </Refs>\n'
                f'                    </TxDtls>\n'
                f'                </NtryDtls>\n'
                f'            </Ntry>\n'
            )
        xml_content += '        </Ntfctn>\n'

        xml_content += f'    </{root_tag}>\n</Document>'
        return xml_content