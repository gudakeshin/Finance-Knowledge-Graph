from enum import Enum

class FinancialDomain(str, Enum):
    ACCOUNTING = "accounting"
    INVESTMENT = "investment"
    TAX = "tax"
    BANKING = "banking"
    INSURANCE = "insurance"
    OTHER = "other" 