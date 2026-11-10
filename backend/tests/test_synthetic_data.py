from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.parsers.pain_001 import Pain001Parser
from app.services.synthetic_data import (
    BANK_PROFILES,
    SyntheticPaymentGenerator,
    generate_pain001_xml,
    is_valid_iban_checksum,
    is_valid_synthetic_routing_pair,
)


def test_generator_is_reproducible_for_same_seed_and_date():
    payment_date = date.today()

    first = SyntheticPaymentGenerator(seed=42).generate(10, payment_date)
    second = SyntheticPaymentGenerator(seed=42).generate(10, payment_date)

    assert first == second


def test_generated_payments_have_valid_test_routing_pairs_and_amounts():
    payments = SyntheticPaymentGenerator(seed=5).generate(50)

    assert len(payments) == 50
    for payment in payments:
        bank_code = payment.debtor_iban[4:12]
        assert payment.debtor_bic == BANK_PROFILES[bank_code]
        assert is_valid_synthetic_routing_pair(
            payment.debtor_bic, payment.debtor_iban
        )
        assert payment.debtor_iban.startswith("DE")
        assert len(payment.debtor_iban) == 22
        assert is_valid_iban_checksum(payment.debtor_iban)
        assert is_valid_iban_checksum(payment.creditor_iban)
        assert Decimal("0.01") <= payment.amount <= Decimal("5000.00")
        assert payment.debtor_name.startswith("Test Payer ")
        assert payment.creditor_name.startswith("Example Merchant ")


def test_generated_pain001_round_trips_through_existing_parser():
    payments = SyntheticPaymentGenerator(seed=7).generate(4)

    xml_content = generate_pain001_xml(payments).encode("utf-8")
    parsed = Pain001Parser(xml_content).get_transactions()

    assert len(parsed) == len(payments)
    for generated, transaction in zip(payments, parsed):
        assert transaction["instruction_id"] == generated.instruction_id
        assert transaction["end_to_end_id"] == generated.end_to_end_id
        assert transaction["amount"] == float(generated.amount)
        assert transaction["currency"] == "EUR"
        assert transaction["bic"] == generated.debtor_bic
        assert transaction["iban"] == generated.debtor_iban
        assert transaction["creditor_name"] == generated.creditor_name
        assert transaction["remittance_info"] == generated.remittance_info


@pytest.mark.parametrize("count", [0, -1, 501])
def test_generator_rejects_counts_outside_supported_range(count):
    with pytest.raises(ValueError, match="count must be between"):
        SyntheticPaymentGenerator().generate(count)


def test_xml_generator_rejects_empty_payments():
    with pytest.raises(ValueError, match="at least one payment"):
        generate_pain001_xml([])


def test_iban_checksum_rejects_invalid_values():
    assert not is_valid_iban_checksum("DE00000000000000000000")
    assert not is_valid_iban_checksum("not-an-iban")
    assert not is_valid_iban_checksum("DE00" + "\uFF10" * 18)


def test_synthetic_routing_pair_rejects_unknown_or_mismatched_bank():
    payment = SyntheticPaymentGenerator(seed=1).generate(1)[0]

    assert not is_valid_synthetic_routing_pair("OTHERBIC", payment.debtor_iban)
    assert not is_valid_synthetic_routing_pair(payment.debtor_bic, "GB00")


def test_generator_rejects_execution_dates_outside_supported_window():
    generator = SyntheticPaymentGenerator()

    with pytest.raises(ValueError, match="execution_date"):
        generator.generate(1, date.today() - timedelta(days=31))
