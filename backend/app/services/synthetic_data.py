"""Generate deterministic, test-only ISO 20022 payment data."""

import argparse
import random
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

PAIN001_NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
MAX_PAYMENT_COUNT = 500

# These are synthetic routing pairs for local testing, not production bank details.
BANK_PROFILES = {
    "99000001": "TSTXDEFF",
    "99000002": "SYNXDEFF",
}


@dataclass(frozen=True)
class SyntheticPayment:
    instruction_id: str
    end_to_end_id: str
    amount: Decimal
    currency: str
    execution_date: date
    debtor_name: str
    debtor_iban: str
    debtor_bic: str
    creditor_name: str
    creditor_iban: str
    remittance_info: str


def _mod97(value: str) -> int:
    remainder = 0
    for character in value:
        numeric = str(ord(character) - ord("A") + 10) if character.isalpha() else character
        for digit in numeric:
            remainder = (remainder * 10 + int(digit)) % 97
    return remainder


def is_valid_iban_checksum(iban: str) -> bool:
    """Check the IBAN mod-97 checksum; this does not verify account ownership."""
    normalized = iban.replace(" ", "").upper()
    if not normalized.isascii() or not 15 <= len(normalized) <= 34:
        return False
    if not normalized.isalnum():
        return False
    if not normalized[:2].isalpha() or not normalized[2:4].isdigit():
        return False
    return _mod97(normalized[4:] + normalized[:4]) == 1


def is_valid_synthetic_routing_pair(bic: str, iban: str) -> bool:
    """Check that a generated German IBAN uses the bank profile for its BIC."""
    normalized_iban = iban.replace(" ", "").upper()
    if (
        len(normalized_iban) != 22
        or not normalized_iban.startswith("DE")
        or not is_valid_iban_checksum(normalized_iban)
    ):
        return False
    return BANK_PROFILES.get(normalized_iban[4:12]) == bic


def _make_german_iban(bank_code: str, account_number: str) -> str:
    if len(bank_code) != 8 or not bank_code.isdigit():
        raise ValueError("German bank code must contain exactly 8 digits")
    if len(account_number) != 10 or not account_number.isdigit():
        raise ValueError("German account number must contain exactly 10 digits")

    bban = bank_code + account_number
    check_digits = 98 - _mod97(bban + "131400")
    return f"DE{check_digits:02d}{bban}"


class SyntheticPaymentGenerator:
    """Create reproducible German payment samples with synthetic routing values."""

    def __init__(self, seed: int = 0):
        self._random = random.Random(seed)

    def generate(
        self, count: int = 25, execution_date: Optional[date] = None
    ) -> list[SyntheticPayment]:
        if not 1 <= count <= MAX_PAYMENT_COUNT:
            raise ValueError(f"count must be between 1 and {MAX_PAYMENT_COUNT}")

        today = date.today()
        payment_date = execution_date or today
        if not today <= payment_date <= today + timedelta(days=30):
            raise ValueError("execution_date must be today or within the next 30 days")

        payments = []
        bank_codes = tuple(BANK_PROFILES)
        for index in range(1, count + 1):
            bank_code = self._random.choice(bank_codes)
            debtor_account = f"{self._random.randrange(10**10):010d}"
            creditor_bank_code = self._random.choice(bank_codes)
            creditor_account = f"{self._random.randrange(10**10):010d}"
            payment_id = f"SYN-{index:06d}"

            payments.append(
                SyntheticPayment(
                    instruction_id=payment_id,
                    end_to_end_id=payment_id,
                    amount=Decimal(self._random.randrange(1, 500_001)) / 100,
                    currency="EUR",
                    execution_date=payment_date,
                    debtor_name=f"Test Payer {index:04d}",
                    debtor_iban=_make_german_iban(bank_code, debtor_account),
                    debtor_bic=BANK_PROFILES[bank_code],
                    creditor_name=f"Example Merchant {index:04d}",
                    creditor_iban=_make_german_iban(
                        creditor_bank_code, creditor_account
                    ),
                    remittance_info=f"Synthetic test invoice INV-{index:06d}",
                )
            )
        return payments


def generate_pain001_xml(
    payments: list[SyntheticPayment], created_at: Optional[datetime] = None
) -> str:
    if not payments:
        raise ValueError("at least one payment is required")

    root = ET.Element(f"{{{PAIN001_NAMESPACE}}}Document")
    initiation = ET.SubElement(root, f"{{{PAIN001_NAMESPACE}}}CstmrCdtTrfInitn")
    group_header = ET.SubElement(initiation, f"{{{PAIN001_NAMESPACE}}}GrpHdr")
    ET.SubElement(group_header, f"{{{PAIN001_NAMESPACE}}}MsgId").text = (
        f"SYNTH-{payments[0].execution_date:%Y%m%d}"
    )
    timestamp = created_at or datetime.combine(payments[0].execution_date, time.min)
    ET.SubElement(group_header, f"{{{PAIN001_NAMESPACE}}}CreDtTm").text = (
        timestamp.isoformat(timespec="seconds")
    )
    ET.SubElement(group_header, f"{{{PAIN001_NAMESPACE}}}NbOfTxs").text = str(
        len(payments)
    )
    ET.SubElement(group_header, f"{{{PAIN001_NAMESPACE}}}CtrlSum").text = str(
        sum((payment.amount for payment in payments), Decimal("0.00"))
    )
    initiating_party = ET.SubElement(
        group_header, f"{{{PAIN001_NAMESPACE}}}InitgPty"
    )
    ET.SubElement(initiating_party, f"{{{PAIN001_NAMESPACE}}}Nm").text = (
        "Synthetic Test Platform"
    )

    for payment in payments:
        payment_info = ET.SubElement(initiation, f"{{{PAIN001_NAMESPACE}}}PmtInf")
        ET.SubElement(payment_info, f"{{{PAIN001_NAMESPACE}}}PmtInfId").text = (
            f"PMT-{payment.instruction_id}"
        )
        ET.SubElement(payment_info, f"{{{PAIN001_NAMESPACE}}}PmtMtd").text = "TRF"
        ET.SubElement(payment_info, f"{{{PAIN001_NAMESPACE}}}ReqdExctnDt").text = (
            payment.execution_date.isoformat()
        )

        debtor = ET.SubElement(payment_info, f"{{{PAIN001_NAMESPACE}}}Dbtr")
        ET.SubElement(debtor, f"{{{PAIN001_NAMESPACE}}}Nm").text = payment.debtor_name
        debtor_account = ET.SubElement(
            payment_info, f"{{{PAIN001_NAMESPACE}}}DbtrAcct"
        )
        debtor_account_id = ET.SubElement(
            debtor_account, f"{{{PAIN001_NAMESPACE}}}Id"
        )
        ET.SubElement(debtor_account_id, f"{{{PAIN001_NAMESPACE}}}IBAN").text = (
            payment.debtor_iban
        )
        debtor_agent = ET.SubElement(
            payment_info, f"{{{PAIN001_NAMESPACE}}}DbtrAgt"
        )
        debtor_financial_id = ET.SubElement(
            ET.SubElement(debtor_agent, f"{{{PAIN001_NAMESPACE}}}FinInstnId"),
            f"{{{PAIN001_NAMESPACE}}}BIC",
        )
        debtor_financial_id.text = payment.debtor_bic

        transaction = ET.SubElement(
            payment_info, f"{{{PAIN001_NAMESPACE}}}CdtTrfTxInf"
        )
        payment_id = ET.SubElement(transaction, f"{{{PAIN001_NAMESPACE}}}PmtId")
        ET.SubElement(payment_id, f"{{{PAIN001_NAMESPACE}}}InstrId").text = (
            payment.instruction_id
        )
        ET.SubElement(payment_id, f"{{{PAIN001_NAMESPACE}}}EndToEndId").text = (
            payment.end_to_end_id
        )
        amount = ET.SubElement(
            ET.SubElement(transaction, f"{{{PAIN001_NAMESPACE}}}Amt"),
            f"{{{PAIN001_NAMESPACE}}}InstdAmt",
            {"Ccy": payment.currency},
        )
        amount.text = f"{payment.amount:.2f}"
        creditor = ET.SubElement(transaction, f"{{{PAIN001_NAMESPACE}}}Cdtr")
        ET.SubElement(creditor, f"{{{PAIN001_NAMESPACE}}}Nm").text = (
            payment.creditor_name
        )
        creditor_account = ET.SubElement(
            transaction, f"{{{PAIN001_NAMESPACE}}}CdtrAcct"
        )
        creditor_account_id = ET.SubElement(
            creditor_account, f"{{{PAIN001_NAMESPACE}}}Id"
        )
        ET.SubElement(creditor_account_id, f"{{{PAIN001_NAMESPACE}}}IBAN").text = (
            payment.creditor_iban
        )
        remittance = ET.SubElement(
            transaction, f"{{{PAIN001_NAMESPACE}}}RmtInf"
        )
        ET.SubElement(remittance, f"{{{PAIN001_NAMESPACE}}}Ustrd").text = (
            payment.remittance_info
        )

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a test-only synthetic German pain.001 payment file."
    )
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payments = SyntheticPaymentGenerator(seed=args.seed).generate(count=args.count)
    xml_content = generate_pain001_xml(payments)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(xml_content, encoding="utf-8")
    print(f"Generated {len(payments)} synthetic payments at {args.output}")


if __name__ == "__main__":
    main()
