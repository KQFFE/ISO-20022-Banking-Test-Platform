import pytest
from app.parsers.pain_001 import Pain001Parser
from app.parsers.validator import ISO20022Validator

def test_pain_001_parser_extraction():
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
        <CstmrCdtTrfInitn>
            <GrpHdr><MsgId>TEST-MSG</MsgId></GrpHdr>
            <PmtInf>
                <DbtrAgt><FinInstnId><BIC>TESTBICC</BIC></FinInstnId></DbtrAgt>
                <DbtrAcct><Id><IBAN>DE12345</IBAN></Id></DbtrAcct>
                <CdtTrfTxInf>
                    <PmtId><InstrId>TX-123</InstrId></PmtId>
                    <Amt><InstdAmt Ccy="EUR">500.00</InstdAmt></Amt>
                </CdtTrfTxInf>
            </PmtInf>
        </CstmrCdtTrfInitn>
    </Document>"""
    
    parser = Pain001Parser(xml_content)
    txs = parser.get_transactions()
    
    assert len(txs) == 1
    assert txs[0]["instruction_id"] == "TX-123"
    assert txs[0]["amount"] == 500.0
    assert txs[0]["bic"] == "TESTBICC"
    assert txs[0]["iban"] == "DE12345"

def test_pain_001_multiple_transactions():
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
        <CstmrCdtTrfInitn>
            <GrpHdr><MsgId>MULTIPLE-TX</MsgId></GrpHdr>
            <PmtInf>
                <DbtrAgt><FinInstnId><BIC>TESTBICC</BIC></FinInstnId></DbtrAgt>
                <DbtrAcct><Id><IBAN>DE123</IBAN></Id></DbtrAcct>
                <CdtTrfTxInf>
                    <PmtId><InstrId>TX-1</InstrId></PmtId>
                    <Amt><InstdAmt Ccy="EUR">100</InstdAmt></Amt>
                </CdtTrfTxInf>
                <CdtTrfTxInf>
                    <PmtId><InstrId>TX-2</InstrId></PmtId>
                    <Amt><InstdAmt Ccy="USD">200</InstdAmt></Amt>
                </CdtTrfTxInf>
            </PmtInf>
        </CstmrCdtTrfInitn>
    </Document>"""
    
    parser = Pain001Parser(xml_content)
    txs = parser.get_transactions()
    
    assert len(txs) == 2
    assert txs[0]["instruction_id"] == "TX-1"
    assert txs[0]["currency"] == "EUR"
    assert txs[1]["instruction_id"] == "TX-2"
    assert txs[1]["currency"] == "USD"

def test_iso_validator_bic():
    allowed = ["BICC123", "BICC456"]
    assert ISO20022Validator.validate_bic("BICC123", allowed) is True
    assert ISO20022Validator.validate_bic("WRONG", allowed) is False
    # Empty list should pass (no restriction)
    assert ISO20022Validator.validate_bic("ANYTHING", []) is True

def test_iso_validator_iban_patterns():
    patterns = ["DE%", "FR123"]
    assert ISO20022Validator.validate_iban("DE998877", patterns) is True
    assert ISO20022Validator.validate_iban("FR123", patterns) is True
    assert ISO20022Validator.validate_iban("GB123", patterns) is False

def test_iso_validator_currency():
    assert ISO20022Validator.validate_currency("EUR", "EUR") is True
    assert ISO20022Validator.validate_currency(" eur ", "EUR") is True
    assert ISO20022Validator.validate_currency("SEK", "EUR") is False
    assert ISO20022Validator.validate_currency("EUR", "") is True

def test_iso_validator_edge_cases():
    # BIC/IBAN None check
    assert ISO20022Validator.validate_bic(None, ["SOME"]) is False
    assert ISO20022Validator.validate_iban(None, ["SOME"]) is False
    
    # Date missing
    assert "missing" in ISO20022Validator.validate_date(None, True, True)[0]
    
    # Invalid date format
    assert "Invalid date format" in ISO20022Validator.validate_date("not-a-date", True, True)[0]
    
    # Back-dating restriction
    past_date = "2020-01-01"
    assert "Back-dating is not permitted" in ISO20022Validator.validate_date(past_date, False, True)[0]
    assert "too old" in ISO20022Validator.validate_date(past_date, True, True)[0]
    
    # Future-dating restriction
    future_date = "2050-01-01"
    assert "Future-dating is not permitted" in ISO20022Validator.validate_date(future_date, True, False)[0]
    assert "too far in the future" in ISO20022Validator.validate_date(future_date, True, True)[0]