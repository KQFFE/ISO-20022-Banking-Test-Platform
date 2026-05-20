from typing import List, Any
from datetime import datetime, date

class ISO20022Validator:
    """
    Utility class for validating ISO 20022 data points against Flow rules.
    """

    @staticmethod
    def validate_bic(bic: str, allowed_bics: List[str]) -> bool:
        """
        Checks if the provided BIC is in the allowed list. 
        If no list is provided, validation passes.
        """
        if not allowed_bics:
            return True
        if bic is None:
            return False
        return bic in allowed_bics

    @staticmethod
    def validate_iban(iban: str, allowed_patterns: List[str]) -> bool:
        """
        Validates an IBAN against allowed patterns.
        Supports prefix matching if the pattern ends with '%'.
        """
        if not allowed_patterns:
            return True
        if iban is None:
            return False
        
        for pattern in allowed_patterns:
            if pattern.endswith('%'):
                if iban.startswith(pattern[:-1]):
                    return True
            elif iban == pattern:
                return True
        return False

    @staticmethod
    def validate_date(tx_date: Any, allow_back_dated: bool, allow_future_dated: bool) -> List[str]:
        """
        Validates the transaction date against flow configuration.
        Supports date objects or ISO format strings.
        """
        if tx_date is None:
            return ["Transaction date (Execution/Booking) is missing"]

        if isinstance(tx_date, str):
            try:
                # Extract YYYY-MM-DD from string
                tx_date = datetime.strptime(tx_date[:10], "%Y-%m-%d").date()
            except ValueError:
                return [f"Invalid date format: {tx_date}"]
        elif isinstance(tx_date, datetime):
            tx_date = tx_date.date()

        today = date.today()
        delta_days = (tx_date - today).days
        errors = []

        if delta_days < 0:
            if not allow_back_dated:
                errors.append(f"Back-dating is not permitted for this flow (Date: {tx_date})")
            elif delta_days < -30:
                errors.append(f"Transaction is too old. Limit is 30 days back (Date: {tx_date})")
        elif delta_days > 0:
            if not allow_future_dated:
                errors.append(f"Future-dating is not permitted for this flow (Date: {tx_date})")
            elif delta_days > 30:
                errors.append(f"Transaction is too far in the future. Limit is 30 days ahead (Date: {tx_date})")

        return errors