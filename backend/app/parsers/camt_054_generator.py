import xml.sax.saxutils as saxutils
from datetime import datetime
from .base_interfaces import BaseGenerator

class Camt054Generator(BaseGenerator):
    """Generates CAMT.054 Bank-to-Customer Debit/Credit Notification XML."""

    def generate_xml(self, tx_data: dict, flow_data: dict) -> str:
        tx = tx_data['transaction']
        raw_data_content = tx_data['raw_data_content']
        transactions_list = tx_data['transactions_list']
        batch_total = tx_data['batch_total']
        batch_count = tx_data['batch_count']
        # Determine summary indicator from the first transaction, default to CRDT
        summary_ind = transactions_list[0].get("credit_debit_indicator", "CRDT") if transactions_list else "CRDT"

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
            f'                    <CdtDbtInd>{summary_ind}</CdtDbtInd>\n'
            f'                </TtlNtries>\n'
            f'            </TxsSummry>\n'
        )
        items = transactions_list if transactions_list else [{"amount": tx.amount, "currency": tx.currency, "instruction_id": tx.instruction_id}]
        for item in items:
            amt = float(item.get("amount", 0))
            ccy = saxutils.escape(str(item.get("currency", tx.currency)))
            e2e = saxutils.escape(str(item.get("end_to_end_id") or item.get("instruction_id") or tx.instruction_id))
            ntry_ref = saxutils.escape(str(item.get("instruction_id", "N/A")))
            bookg_dt = saxutils.escape(str(item.get("date") or datetime.now().strftime("%Y-%m-%d"))) # Use parsed date
            val_dt = saxutils.escape(str(item.get("value_date") or bookg_dt)) # Use parsed value date
            cdt_dbt_ind = saxutils.escape(str(item.get("credit_debit_indicator", "CRDT")))
            dbtr_nm = saxutils.escape(str(item.get("debtor_name", "Unknown")))
            dbtr_addr_ctry = saxutils.escape(str(item.get("debtor_address_country", "")))
            dbtr_addr_lines = item.get("debtor_address_lines", [])
            remittance_info_dict = item.get("remittance_info", {})
            acct_svcr_ref = saxutils.escape(str(item.get("acct_svcr_ref", "")))
            bk_tx_domn_cd = saxutils.escape(str(item.get("bank_transaction_code_domain", "PMNT")))
            bk_tx_fmly_cd = saxutils.escape(str(item.get("bank_transaction_code_family", "RCDT")))
            bk_tx_subfmly_cd = saxutils.escape(str(item.get("bank_transaction_code_subfamily", "ESCT")))
            acceptance_date_time = saxutils.escape(str(item.get("acceptance_date_time", "")))
            
            xml_content += (
                f'            <Ntry>\n'
                f'                <NtryRef>{ntry_ref}</NtryRef>\n'
                f'                <Amt Ccy="{ccy}">{amt:.2f}</Amt>\n'
                f'                <CdtDbtInd>{cdt_dbt_ind}</CdtDbtInd>\n'
                f'                <Sts>BOOK</Sts>\n'
                f'                <BookgDt><Dt>{bookg_dt}</Dt></BookgDt>\n'
                f'                <ValDt><Dt>{val_dt}</Dt></ValDt>\n'
                f'                <AcctSvcrRef>{acct_svcr_ref}</AcctSvcrRef>\n'
                f'                <BkTxCd>\n'
                f'                    <Domn>\n'
                f'                        <Cd>{bk_tx_domn_cd}</Cd>\n'
                f'                        <Fmly>\n'
                f'                            <Cd>{bk_tx_fmly_cd}</Cd>\n'
                f'                            <SubFmlyCd>{bk_tx_subfmly_cd}</SubFmlyCd>\n'
                f'                        </Fmly>\n'
                f'                    </Domn>\n'
                f'                </BkTxCd>\n'
                f'                <NtryDtls>\n'
                f'                    <TxDtls>\n'
                f'                        <Refs>\n'
                f'                            <EndToEndId>{e2e}</EndToEndId>\n'
                f'                        </Refs>\n'
                f'                        <RltdPties>\n'
                f'                            <Dbtr>\n'
                f'                                <Nm>{dbtr_nm}</Nm>\n'
                f'                                <PstlAdr>\n'
                f'                                    <Ctry>{dbtr_addr_ctry}</Ctry>\n'
            )
            for line in dbtr_addr_lines:
                xml_content += f'                                    <AdrLine>{saxutils.escape(line)}</AdrLine>\n'
            xml_content += (
                f'                                </PstlAdr>\n'
                f'                            </Dbtr>\n'
                f'                        </RltdPties>\n'
            )

            # Remittance Information
            if remittance_info_dict:
                xml_content += f'                        <RmtInf>\n'
                if remittance_info_dict.get('unstructured'):
                    for ustrd_line in remittance_info_dict['unstructured']:
                        xml_content += f'                            <Ustrd>{saxutils.escape(ustrd_line)}</Ustrd>\n'
                if remittance_info_dict.get('structured'):
                    strd_ref = saxutils.escape(str(remittance_info_dict['structured'].get('CdtrRefInf', '')))
                    xml_content += (
                        f'                            <Strd>\n'
                        f'                                <CdtrRefInf>\n'
                        f'                                    <Ref>{strd_ref}</Ref>\n'
                        f'                                </CdtrRefInf>\n'
                        f'                            </Strd>\n'
                    )
                xml_content += f'                        </RmtInf>\n'

            if acceptance_date_time:
                xml_content += (
                    f'                        <RltdDts>\n'
                    f'                            <AccptncDtTm>{acceptance_date_time}</AccptncDtTm>\n'
                    f'                        </RltdDts>\n'
                )
            xml_content += (
                f'                    </TxDtls>\n'
                f'                </NtryDtls>\n'
                f'            </Ntry>\n'
            )
        xml_content += '        </Ntfctn>\n'

        xml_content += f'    </{root_tag}>\n</Document>'
        return xml_content
