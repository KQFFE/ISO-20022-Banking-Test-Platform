import xml.sax.saxutils as saxutils
from datetime import datetime
from .base_interfaces import BaseGenerator # Import BaseGenerator

class Pain001Generator(BaseGenerator):
    """Generates Pain.001 Customer Credit Transfer Initiation XML."""

    def generate_xml(self, tx_data: dict, flow_data: dict) -> str:
        tx = tx_data['transaction']
        raw_data_content = tx_data['raw_data_content']
        transactions_list = tx_data['transactions_list']
        batch_total = tx_data['batch_total']
        batch_count = tx_data['batch_count']

        cre_dt_tm = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        ns = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
        root_tag = "CstmrCdtTrfInitn"

        xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="{ns}">\n    <{root_tag}>\n'

        xml_content += (
            f'        <GrpHdr>\n'
            f'            <MsgId>EXEC-{tx.instruction_id}</MsgId>\n'
            f'            <CreDtTm>{cre_dt_tm}</CreDtTm>\n'
            f'            <NbOfTxs>{batch_count}</NbOfTxs>\n'
            f'            <CtrlSum>{float(batch_total):.2f}</CtrlSum>\n'
        )
        # Placeholder for InitgPty details if needed
        xml_content += f'            <InitgPty><Nm>Generated Test Platform</Nm></InitgPty>\n'
        xml_content += f'        </GrpHdr>\n'

        items = transactions_list if transactions_list else [{"amount": tx.amount, "currency": tx.currency, "instruction_id": tx.instruction_id, "date": raw_data_content.get("date")}]
        for item in items:
            amt = float(item.get("amount", 0))
            ccy = saxutils.escape(str(item.get("currency", tx.currency)))
            e2e = saxutils.escape(str(item.get("end_to_end_id") or item.get("instruction_id") or tx.instruction_id))
            tx_date = item.get("date") or datetime.now().strftime("%Y-%m-%d")
            iban = saxutils.escape(str(raw_data_content.get("iban", "N/A"))) # Assuming debtor IBAN is stored in raw_data
            
            xml_content += (
                f'        <PmtInf>\n'
                f'            <PmtInfId>PMT-{e2e}</PmtInfId>\n'
                f'            <PmtMtd>TRF</PmtMtd>\n'
                f'            <ReqdExctnDt>{tx_date}</ReqdExctnDt>\n'
                f'            <DbtrAcct><Id><IBAN>{iban}</IBAN></Id></DbtrAcct>\n'
                f'            <CdtTrfTxInf>\n'
                f'                <PmtId><EndToEndId>{e2e}</EndToEndId></PmtId>\n'
                f'                <Amt><InstdAmt Ccy="{ccy}">{amt:.2f}</InstdAmt></Amt>\n'
                f'                <Cdtr><Nm>Creditor Name</Nm></Cdtr>\n' # Placeholder
                f'                <CdtrAcct><Id><IBAN>GB29NWBK60161331926819</IBAN></Id></CdtrAcct>\n' # Placeholder
                f'            </CdtTrfTxInf>\n'
                f'        </PmtInf>\n'
            )

        xml_content += f'    </{root_tag}>\n</Document>'
        return xml_content