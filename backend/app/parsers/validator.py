from typing import List

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