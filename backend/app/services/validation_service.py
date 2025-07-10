from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from enum import Enum
import re
from pydantic import BaseModel, Field
from ..models.graph_models import Entity, Relationship, EntityType, RelationshipType

logger = logging.getLogger(__name__)

class ValidationLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationRule(BaseModel):
    name: str
    description: str
    level: ValidationLevel
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EntityValidationRule(ValidationRule):
    entity_type: EntityType
    required_fields: List[str] = []
    field_patterns: Dict[str, str] = {}
    field_ranges: Dict[str, Tuple[float, float]] = {}
    custom_validators: List[str] = []
    cross_references: List[str] = []
    confidence_threshold: float = 0.7
    uniqueness_constraints: List[str] = []
    temporal_validity: Optional[Dict[str, Any]] = None
    hierarchical_constraints: Optional[Dict[str, Any]] = None
    financial_constraints: Optional[Dict[str, Any]] = None
    regulatory_compliance: Optional[Dict[str, Any]] = None

class RelationshipValidationRule(ValidationRule):
    relationship_type: RelationshipType
    source_entity_type: EntityType
    target_entity_type: EntityType
    required_properties: List[str] = []
    property_patterns: Dict[str, str] = {}
    property_ranges: Dict[str, Tuple[float, float]] = {}
    custom_validators: List[str] = []
    temporal_constraints: Optional[Dict[str, Any]] = None
    cardinality_constraints: Optional[Dict[str, Any]] = None
    financial_constraints: Optional[Dict[str, Any]] = None
    regulatory_compliance: Optional[Dict[str, Any]] = None

class ValidationResult(BaseModel):
    rule_name: str
    level: ValidationLevel
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    suggested_corrections: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    affected_fields: Optional[List[str]] = None
    validation_context: Optional[Dict[str, Any]] = None

class ValidationReport(BaseModel):
    entity_id: Optional[str] = None
    relationship_id: Optional[str] = None
    results: List[ValidationResult]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_status: ValidationLevel
    confidence_score: float
    validation_duration: float
    affected_entities: Optional[List[str]] = None
    affected_relationships: Optional[List[str]] = None
    validation_context: Optional[Dict[str, Any]] = None

    def error_count(self) -> int:
        return len([r for r in self.results if r.level == ValidationLevel.ERROR])

    def warning_count(self) -> int:
        return len([r for r in self.results if r.level == ValidationLevel.WARNING])

    def has_errors(self) -> bool:
        return self.error_count() > 0

    def has_warnings(self) -> bool:
        return self.warning_count() > 0

class FinancialDomain(str, Enum):
    BANKING = "banking"
    INVESTMENT = "investment"
    INSURANCE = "insurance"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    FINTECH = "fintech"
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    WEALTH_MANAGEMENT = "wealth_management"
    HEDGE_FUND = "hedge_fund"
    PRIVATE_EQUITY = "private_equity"
    VENTURE_CAPITAL = "venture_capital"
    ASSET_MANAGEMENT = "asset_management"
    MARKET_MAKING = "market_making"
    QUANTITATIVE_TRADING = "quantitative_trading"

class FinancialValidationRule(EntityValidationRule):
    domain: FinancialDomain
    regulatory_framework: Optional[str] = None
    compliance_requirements: Optional[List[str]] = None
    risk_factors: Optional[Dict[str, Any]] = None
    market_conditions: Optional[Dict[str, Any]] = None
    reporting_requirements: Optional[Dict[str, Any]] = None

class ValidationService:
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self._initialize_default_rules()
        self._initialize_financial_domain_rules()

    def _initialize_default_rules(self):
        # Company validation rules
        self.rules["company_required_fields"] = EntityValidationRule(
            name="company_required_fields",
            description="Required fields for company entities",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.COMPANY,
            required_fields=["name", "industry", "founding_date"],
            field_patterns={
                "ticker": r"^[A-Z]{1,5}$",
                "website": r"^https?://[^\s/$.?#].[^\s]*$"
            },
            uniqueness_constraints=["ticker", "name"],
            financial_constraints={
                "required_metrics": ["revenue", "market_cap", "employees"],
                "metric_ranges": {
                    "revenue": (0, float("inf")),
                    "market_cap": (0, float("inf")),
                    "employees": (1, float("inf"))
                }
            }
        )

        # Person validation rules
        self.rules["person_required_fields"] = EntityValidationRule(
            name="person_required_fields",
            description="Required fields for person entities",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.PERSON,
            required_fields=["name", "role"],
            field_patterns={
                "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "phone": r"^\+?[1-9]\d{1,14}$"
            },
            temporal_validity={
                "start_date": "birth_date",
                "end_date": "death_date"
            }
        )

        # Financial Instrument validation rules
        self.rules["financial_instrument_required_fields"] = EntityValidationRule(
            name="financial_instrument_required_fields",
            description="Required fields for financial instrument entities",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.FINANCIAL_INSTRUMENT,
            required_fields=["name", "type", "issuer"],
            field_patterns={
                "isin": r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",
                "cusip": r"^[0-9A-Z]{9}$"
            },
            financial_constraints={
                "required_metrics": ["face_value", "maturity_date"],
                "metric_ranges": {
                    "face_value": (0, float("inf")),
                    "coupon_rate": (0, 100)
                }
            },
            regulatory_compliance={
                "required_documents": ["prospectus", "offering_memorandum"],
                "reporting_requirements": ["quarterly_reports", "annual_reports"]
            }
        )

        # Transaction validation rules
        self.rules["transaction_required_fields"] = EntityValidationRule(
            name="transaction_required_fields",
            description="Required fields for transaction entities",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.TRANSACTION,
            required_fields=["amount", "date", "type"],
            financial_constraints={
                "required_metrics": ["amount", "currency", "exchange_rate"],
                "metric_ranges": {
                    "amount": (0, float("inf")),
                    "exchange_rate": (0, float("inf"))
                }
            },
            temporal_validity={
                "start_date": "transaction_date",
                "end_date": "settlement_date"
            }
        )

        # Relationship validation rules
        self.rules["company_person_relationship"] = RelationshipValidationRule(
            name="company_person_relationship",
            description="Validation rules for company-person relationships",
            level=ValidationLevel.ERROR,
            relationship_type=RelationshipType.EMPLOYMENT,
            source_entity_type=EntityType.COMPANY,
            target_entity_type=EntityType.PERSON,
            required_properties=["start_date", "role"],
            temporal_constraints={
                "start_date": "required",
                "end_date": "optional"
            },
            cardinality_constraints={
                "max_roles_per_person": 1,
                "max_companies_per_role": 1
            }
        )

        self.rules["company_financial_instrument"] = RelationshipValidationRule(
            name="company_financial_instrument",
            description="Validation rules for company-financial instrument relationships",
            level=ValidationLevel.ERROR,
            relationship_type=RelationshipType.ISSUES,
            source_entity_type=EntityType.COMPANY,
            target_entity_type=EntityType.FINANCIAL_INSTRUMENT,
            required_properties=["issue_date", "issue_price"],
            financial_constraints={
                "required_metrics": ["issue_price", "issue_size"],
                "metric_ranges": {
                    "issue_price": (0, float("inf")),
                    "issue_size": (0, float("inf"))
                }
            },
            regulatory_compliance={
                "required_documents": ["offering_document", "regulatory_filing"],
                "reporting_requirements": ["disclosure_requirements"]
            }
        )

        self.rules["transaction_relationship"] = RelationshipValidationRule(
            name="transaction_relationship",
            description="Validation rules for transaction relationships",
            level=ValidationLevel.ERROR,
            relationship_type=RelationshipType.TRANSACTION,
            source_entity_type=EntityType.PERSON,
            target_entity_type=EntityType.FINANCIAL_INSTRUMENT,
            required_properties=["transaction_date", "amount", "currency"],
            financial_constraints={
                "required_metrics": ["amount", "currency", "exchange_rate"],
                "metric_ranges": {
                    "amount": (0, float("inf")),
                    "exchange_rate": (0, float("inf"))
                }
            },
            temporal_constraints={
                "transaction_date": "required",
                "settlement_date": "required"
            }
        )

    def _initialize_financial_domain_rules(self):
        # Banking domain rules
        self.rules["banking_account_validation"] = FinancialValidationRule(
            name="banking_account_validation",
            description="Validation rules for banking accounts",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.ACCOUNT,
            domain=FinancialDomain.BANKING,
            required_fields=["account_number", "account_type", "currency", "balance"],
            field_patterns={
                "account_number": r"^[A-Z0-9]{8,20}$",
                "iban": r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$",
                "swift_code": r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$"
            },
            financial_constraints={
                "required_metrics": ["balance", "interest_rate", "overdraft_limit"],
                "metric_ranges": {
                    "balance": (-float("inf"), float("inf")),
                    "interest_rate": (0, 100),
                    "overdraft_limit": (0, float("inf"))
                }
            },
            regulatory_framework="Basel III",
            compliance_requirements=[
                "KYC",
                "AML",
                "Transaction Monitoring",
                "Risk Assessment"
            ],
            risk_factors={
                "credit_risk": True,
                "operational_risk": True,
                "market_risk": True,
                "liquidity_risk": True
            }
        )

        # Investment domain rules
        self.rules["investment_portfolio_validation"] = FinancialValidationRule(
            name="investment_portfolio_validation",
            description="Validation rules for investment portfolios",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.PORTFOLIO,
            domain=FinancialDomain.INVESTMENT,
            required_fields=["portfolio_id", "investor_id", "risk_profile", "investment_strategy"],
            financial_constraints={
                "required_metrics": ["total_value", "risk_score", "diversification_ratio"],
                "metric_ranges": {
                    "total_value": (0, float("inf")),
                    "risk_score": (1, 10),
                    "diversification_ratio": (0, 1)
                }
            },
            regulatory_framework="MiFID II",
            compliance_requirements=[
                "Suitability Assessment",
                "Best Execution",
                "Transaction Reporting",
                "Client Categorization"
            ],
            risk_factors={
                "market_risk": True,
                "credit_risk": True,
                "liquidity_risk": True,
                "concentration_risk": True
            }
        )

        # Insurance domain rules
        self.rules["insurance_policy_validation"] = FinancialValidationRule(
            name="insurance_policy_validation",
            description="Validation rules for insurance policies",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.POLICY,
            domain=FinancialDomain.INSURANCE,
            required_fields=["policy_number", "coverage_type", "premium", "coverage_amount"],
            field_patterns={
                "policy_number": r"^[A-Z0-9]{10,15}$",
                "coverage_type": r"^(LIFE|HEALTH|PROPERTY|LIABILITY|AUTO)$"
            },
            financial_constraints={
                "required_metrics": ["premium", "coverage_amount", "deductible"],
                "metric_ranges": {
                    "premium": (0, float("inf")),
                    "coverage_amount": (0, float("inf")),
                    "deductible": (0, float("inf"))
                }
            },
            regulatory_framework="Solvency II",
            compliance_requirements=[
                "Policy Documentation",
                "Risk Assessment",
                "Claims Processing",
                "Reserve Requirements"
            ],
            risk_factors={
                "underwriting_risk": True,
                "reserve_risk": True,
                "catastrophe_risk": True,
                "operational_risk": True
            }
        )

        # Real Estate domain rules
        self.rules["real_estate_property_validation"] = FinancialValidationRule(
            name="real_estate_property_validation",
            description="Validation rules for real estate properties",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.PROPERTY,
            domain=FinancialDomain.REAL_ESTATE,
            required_fields=["property_id", "address", "property_type", "valuation"],
            field_patterns={
                "property_id": r"^[A-Z0-9]{8,12}$",
                "property_type": r"^(RESIDENTIAL|COMMERCIAL|INDUSTRIAL|LAND)$"
            },
            financial_constraints={
                "required_metrics": ["valuation", "rental_income", "operating_expenses"],
                "metric_ranges": {
                    "valuation": (0, float("inf")),
                    "rental_income": (0, float("inf")),
                    "operating_expenses": (0, float("inf"))
                }
            },
            regulatory_framework="Real Estate Regulations",
            compliance_requirements=[
                "Property Documentation",
                "Valuation Standards",
                "Environmental Assessment",
                "Zoning Compliance"
            ],
            risk_factors={
                "market_risk": True,
                "location_risk": True,
                "environmental_risk": True,
                "legal_risk": True
            }
        )

        # Crypto domain rules
        self.rules["crypto_asset_validation"] = FinancialValidationRule(
            name="crypto_asset_validation",
            description="Validation rules for crypto assets",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.CRYPTO_ASSET,
            domain=FinancialDomain.CRYPTO,
            required_fields=["asset_id", "blockchain", "token_standard", "total_supply"],
            field_patterns={
                "asset_id": r"^[A-Z0-9]{3,10}$",
                "token_standard": r"^(ERC20|ERC721|ERC1155|BEP20)$"
            },
            financial_constraints={
                "required_metrics": ["market_cap", "circulating_supply", "trading_volume"],
                "metric_ranges": {
                    "market_cap": (0, float("inf")),
                    "circulating_supply": (0, float("inf")),
                    "trading_volume": (0, float("inf"))
                }
            },
            regulatory_framework="Crypto Regulations",
            compliance_requirements=[
                "KYC/AML",
                "Transaction Monitoring",
                "Smart Contract Audit",
                "Security Assessment"
            ],
            risk_factors={
                "market_risk": True,
                "technical_risk": True,
                "regulatory_risk": True,
                "security_risk": True
            }
        )

        # FinTech domain rules
        self.rules["fintech_service_validation"] = FinancialValidationRule(
            name="fintech_service_validation",
            description="Validation rules for fintech services",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.FINTECH_SERVICE,
            domain=FinancialDomain.FINTECH,
            required_fields=["service_id", "service_type", "api_version", "security_level"],
            field_patterns={
                "service_id": r"^[A-Z0-9]{6,12}$",
                "api_version": r"^v[0-9]+\.[0-9]+\.[0-9]+$"
            },
            financial_constraints={
                "required_metrics": ["uptime", "response_time", "error_rate"],
                "metric_ranges": {
                    "uptime": (0, 100),
                    "response_time": (0, 1000),
                    "error_rate": (0, 1)
                }
            },
            regulatory_framework="FinTech Regulations",
            compliance_requirements=[
                "API Security",
                "Data Protection",
                "Service Level Agreement",
                "Incident Response"
            ],
            risk_factors={
                "operational_risk": True,
                "security_risk": True,
                "compliance_risk": True,
                "reputation_risk": True
            }
        )

        # Regulatory domain rules
        self.rules["regulatory_report_validation"] = FinancialValidationRule(
            name="regulatory_report_validation",
            description="Validation rules for regulatory reports",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.REGULATORY_REPORT,
            domain=FinancialDomain.REGULATORY,
            required_fields=["report_id", "report_type", "reporting_period", "submission_date"],
            field_patterns={
                "report_id": r"^[A-Z0-9]{10,15}$",
                "report_type": r"^(FINANCIAL|COMPLIANCE|RISK|AUDIT)$"
            },
            financial_constraints={
                "required_metrics": ["completeness_score", "accuracy_score", "timeliness_score"],
                "metric_ranges": {
                    "completeness_score": (0, 100),
                    "accuracy_score": (0, 100),
                    "timeliness_score": (0, 100)
                }
            },
            regulatory_framework="Regulatory Reporting Standards",
            compliance_requirements=[
                "Data Accuracy",
                "Timely Submission",
                "Documentation",
                "Audit Trail"
            ],
            risk_factors={
                "compliance_risk": True,
                "reporting_risk": True,
                "audit_risk": True,
                "reputation_risk": True
            }
        )

        # Compliance domain rules
        self.rules["compliance_check_validation"] = FinancialValidationRule(
            name="compliance_check_validation",
            description="Validation rules for compliance checks",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.COMPLIANCE_CHECK,
            domain=FinancialDomain.COMPLIANCE,
            required_fields=["check_id", "check_type", "check_date", "status"],
            field_patterns={
                "check_id": r"^[A-Z0-9]{8,12}$",
                "check_type": r"^(KYC|AML|SANCTIONS|PEP|ADVERSE_MEDIA)$"
            },
            financial_constraints={
                "required_metrics": ["risk_score", "confidence_score", "completion_rate"],
                "metric_ranges": {
                    "risk_score": (0, 100),
                    "confidence_score": (0, 100),
                    "completion_rate": (0, 100)
                }
            },
            regulatory_framework="Compliance Standards",
            compliance_requirements=[
                "Risk Assessment",
                "Due Diligence",
                "Documentation",
                "Monitoring"
            ],
            risk_factors={
                "compliance_risk": True,
                "operational_risk": True,
                "reputation_risk": True,
                "legal_risk": True
            }
        )

        # Wealth Management domain rules
        self.rules["wealth_portfolio_validation"] = FinancialValidationRule(
            name="wealth_portfolio_validation",
            description="Validation rules for wealth management portfolios",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.PORTFOLIO,
            domain=FinancialDomain.WEALTH_MANAGEMENT,
            required_fields=["portfolio_id", "client_id", "risk_profile", "investment_strategy", "asset_allocation"],
            financial_constraints={
                "required_metrics": ["total_value", "risk_score", "diversification_ratio", "sharpe_ratio", "alpha"],
                "metric_ranges": {
                    "total_value": (0, float("inf")),
                    "risk_score": (1, 10),
                    "diversification_ratio": (0, 1),
                    "sharpe_ratio": (-float("inf"), float("inf")),
                    "alpha": (-float("inf"), float("inf"))
                }
            },
            regulatory_framework="MiFID II",
            compliance_requirements=[
                "Suitability Assessment",
                "Best Execution",
                "Transaction Reporting",
                "Client Categorization",
                "Portfolio Rebalancing",
                "Performance Attribution"
            ],
            risk_factors={
                "market_risk": True,
                "credit_risk": True,
                "liquidity_risk": True,
                "concentration_risk": True,
                "currency_risk": True,
                "interest_rate_risk": True
            }
        )

        # Hedge Fund domain rules
        self.rules["hedge_fund_validation"] = FinancialValidationRule(
            name="hedge_fund_validation",
            description="Validation rules for hedge funds",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.FUND,
            domain=FinancialDomain.HEDGE_FUND,
            required_fields=["fund_id", "strategy", "aum", "leverage_ratio", "performance_fee", "management_fee"],
            financial_constraints={
                "required_metrics": ["aum", "leverage_ratio", "performance_fee", "management_fee", "sharpe_ratio", "sortino_ratio"],
                "metric_ranges": {
                    "aum": (0, float("inf")),
                    "leverage_ratio": (0, float("inf")),
                    "performance_fee": (0, 50),
                    "management_fee": (0, 5),
                    "sharpe_ratio": (-float("inf"), float("inf")),
                    "sortino_ratio": (-float("inf"), float("inf"))
                }
            },
            regulatory_framework="AIFMD",
            compliance_requirements=[
                "Risk Management",
                "Leverage Limits",
                "Reporting Requirements",
                "Investor Protection",
                "Transparency"
            ],
            risk_factors={
                "market_risk": True,
                "credit_risk": True,
                "liquidity_risk": True,
                "leverage_risk": True,
                "counterparty_risk": True,
                "model_risk": True
            }
        )

        # Private Equity domain rules
        self.rules["private_equity_validation"] = FinancialValidationRule(
            name="private_equity_validation",
            description="Validation rules for private equity funds",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.FUND,
            domain=FinancialDomain.PRIVATE_EQUITY,
            required_fields=["fund_id", "vintage_year", "target_size", "committed_capital", "called_capital", "distributed_capital"],
            financial_constraints={
                "required_metrics": ["irr", "moic", "rvpi", "dvpi", "total_value_to_paid_in"],
                "metric_ranges": {
                    "irr": (-100, float("inf")),
                    "moic": (0, float("inf")),
                    "rvpi": (0, float("inf")),
                    "dvpi": (0, float("inf")),
                    "total_value_to_paid_in": (0, float("inf"))
                }
            },
            regulatory_framework="AIFMD",
            compliance_requirements=[
                "Investment Strategy",
                "Capital Calls",
                "Distributions",
                "Valuation",
                "Reporting"
            ],
            risk_factors={
                "investment_risk": True,
                "valuation_risk": True,
                "liquidity_risk": True,
                "concentration_risk": True,
                "exit_risk": True
            }
        )

        # Venture Capital domain rules
        self.rules["venture_capital_validation"] = FinancialValidationRule(
            name="venture_capital_validation",
            description="Validation rules for venture capital funds",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.FUND,
            domain=FinancialDomain.VENTURE_CAPITAL,
            required_fields=["fund_id", "vintage_year", "target_size", "committed_capital", "called_capital", "portfolio_companies"],
            financial_constraints={
                "required_metrics": ["irr", "moic", "rvpi", "dvpi", "total_value_to_paid_in", "portfolio_diversity_score"],
                "metric_ranges": {
                    "irr": (-100, float("inf")),
                    "moic": (0, float("inf")),
                    "rvpi": (0, float("inf")),
                    "dvpi": (0, float("inf")),
                    "total_value_to_paid_in": (0, float("inf")),
                    "portfolio_diversity_score": (0, 1)
                }
            },
            regulatory_framework="AIFMD",
            compliance_requirements=[
                "Investment Strategy",
                "Capital Calls",
                "Distributions",
                "Valuation",
                "Reporting",
                "Portfolio Management"
            ],
            risk_factors={
                "investment_risk": True,
                "valuation_risk": True,
                "liquidity_risk": True,
                "concentration_risk": True,
                "exit_risk": True,
                "technology_risk": True
            }
        )

        # Asset Management domain rules
        self.rules["asset_management_validation"] = FinancialValidationRule(
            name="asset_management_validation",
            description="Validation rules for asset management firms",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.COMPANY,
            domain=FinancialDomain.ASSET_MANAGEMENT,
            required_fields=["company_id", "aum", "number_of_funds", "investment_strategies", "client_types"],
            financial_constraints={
                "required_metrics": ["aum", "revenue", "profit_margin", "client_retention_rate", "fund_performance"],
                "metric_ranges": {
                    "aum": (0, float("inf")),
                    "revenue": (0, float("inf")),
                    "profit_margin": (0, 100),
                    "client_retention_rate": (0, 100),
                    "fund_performance": (-float("inf"), float("inf"))
                }
            },
            regulatory_framework="UCITS",
            compliance_requirements=[
                "Risk Management",
                "Client Reporting",
                "Performance Attribution",
                "Compliance Monitoring",
                "Client Communication"
            ],
            risk_factors={
                "market_risk": True,
                "operational_risk": True,
                "compliance_risk": True,
                "reputation_risk": True,
                "client_risk": True
            }
        )

        # Market Making domain rules
        self.rules["market_making_validation"] = FinancialValidationRule(
            name="market_making_validation",
            description="Validation rules for market making operations",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.COMPANY,
            domain=FinancialDomain.MARKET_MAKING,
            required_fields=["company_id", "trading_venues", "instruments", "inventory_limits", "risk_limits"],
            financial_constraints={
                "required_metrics": ["inventory_value", "spread", "volume", "profit_loss", "risk_metrics"],
                "metric_ranges": {
                    "inventory_value": (-float("inf"), float("inf")),
                    "spread": (0, float("inf")),
                    "volume": (0, float("inf")),
                    "profit_loss": (-float("inf"), float("inf")),
                    "risk_metrics": (-float("inf"), float("inf"))
                }
            },
            regulatory_framework="MiFID II",
            compliance_requirements=[
                "Best Execution",
                "Market Making Obligations",
                "Risk Management",
                "Reporting",
                "Compliance"
            ],
            risk_factors={
                "market_risk": True,
                "inventory_risk": True,
                "liquidity_risk": True,
                "operational_risk": True,
                "regulatory_risk": True
            }
        )

        # Quantitative Trading domain rules
        self.rules["quantitative_trading_validation"] = FinancialValidationRule(
            name="quantitative_trading_validation",
            description="Validation rules for quantitative trading systems",
            level=ValidationLevel.ERROR,
            entity_type=EntityType.SYSTEM,
            domain=FinancialDomain.QUANTITATIVE_TRADING,
            required_fields=["system_id", "strategy_type", "trading_parameters", "risk_parameters", "performance_metrics"],
            financial_constraints={
                "required_metrics": ["sharpe_ratio", "sortino_ratio", "max_drawdown", "win_rate", "profit_factor"],
                "metric_ranges": {
                    "sharpe_ratio": (-float("inf"), float("inf")),
                    "sortino_ratio": (-float("inf"), float("inf")),
                    "max_drawdown": (-100, 0),
                    "win_rate": (0, 100),
                    "profit_factor": (0, float("inf"))
                }
            },
            regulatory_framework="MiFID II",
            compliance_requirements=[
                "Algorithm Testing",
                "Risk Management",
                "Monitoring",
                "Reporting",
                "Compliance"
            ],
            risk_factors={
                "model_risk": True,
                "execution_risk": True,
                "market_risk": True,
                "operational_risk": True,
                "regulatory_risk": True
            }
        )

    def get_validation_rules(self) -> List[Dict[str, Any]]:
        return [rule.dict() for rule in self.rules.values()]

    def update_validation_rule(self, rule: ValidationRule) -> bool:
        try:
            self.rules[rule.name] = rule
            return True
        except Exception as e:
            logger.error(f"Error updating validation rule: {str(e)}")
            return False

    def validate_entity(self, entity: Entity) -> ValidationReport:
        results = []
        confidence_scores = []
        validation_start = datetime.utcnow()

        # Get applicable rules
        applicable_rules = [
            rule for rule in self.rules.values()
            if isinstance(rule, EntityValidationRule) and rule.entity_type == entity.type
        ]

        for rule in applicable_rules:
            if not rule.enabled:
                continue

            # Validate required fields
            for field in rule.required_fields:
                if field not in entity.properties:
                    results.append(ValidationResult(
                        rule_name=rule.name,
                        level=ValidationLevel.ERROR,
                        message=f"Missing required field: {field}",
                        affected_fields=[field],
                        suggested_corrections=[{
                            "field": field,
                            "action": "add",
                            "description": f"Add the required field {field}"
                        }]
                    ))

            # Validate field patterns
            for field, pattern in rule.field_patterns.items():
                if field in entity.properties:
                    if not re.match(pattern, str(entity.properties[field])):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Field {field} does not match required pattern",
                            affected_fields=[field],
                            suggested_corrections=[{
                                "field": field,
                                "action": "format",
                                "description": f"Format {field} according to pattern: {pattern}"
                            }]
                        ))

            # Validate field ranges
            for field, (min_val, max_val) in rule.field_ranges.items():
                if field in entity.properties:
                    try:
                        value = float(entity.properties[field])
                        if value < min_val or value > max_val:
                            results.append(ValidationResult(
                                rule_name=rule.name,
                                level=ValidationLevel.ERROR,
                                message=f"Field {field} value {value} is outside allowed range [{min_val}, {max_val}]",
                                affected_fields=[field],
                                suggested_corrections=[{
                                    "field": field,
                                    "action": "adjust",
                                    "description": f"Adjust {field} to be within range [{min_val}, {max_val}]"
                                }]
                            ))
                    except (ValueError, TypeError):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Field {field} must be a numeric value",
                            affected_fields=[field],
                            suggested_corrections=[{
                                "field": field,
                                "action": "convert",
                                "description": f"Convert {field} to a numeric value"
                            }]
                        ))

            # Validate financial constraints
            if rule.financial_constraints:
                for metric in rule.financial_constraints.get("required_metrics", []):
                    if metric not in entity.properties:
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Missing required financial metric: {metric}",
                            affected_fields=[metric],
                            suggested_corrections=[{
                                "field": metric,
                                "action": "add",
                                "description": f"Add the required financial metric {metric}"
                            }]
                        ))

                for metric, (min_val, max_val) in rule.financial_constraints.get("metric_ranges", {}).items():
                    if metric in entity.properties:
                        try:
                            value = float(entity.properties[metric])
                            if value < min_val or value > max_val:
                                results.append(ValidationResult(
                                    rule_name=rule.name,
                                    level=ValidationLevel.ERROR,
                                    message=f"Financial metric {metric} value {value} is outside allowed range [{min_val}, {max_val}]",
                                    affected_fields=[metric],
                                    suggested_corrections=[{
                                        "field": metric,
                                        "action": "adjust",
                                        "description": f"Adjust {metric} to be within range [{min_val}, {max_val}]"
                                    }]
                                ))
                        except (ValueError, TypeError):
                            results.append(ValidationResult(
                                rule_name=rule.name,
                                level=ValidationLevel.ERROR,
                                message=f"Financial metric {metric} must be a numeric value",
                                affected_fields=[metric],
                                suggested_corrections=[{
                                    "field": metric,
                                    "action": "convert",
                                    "description": f"Convert {metric} to a numeric value"
                                }]
                            ))

            # Validate regulatory compliance
            if rule.regulatory_compliance:
                for doc in rule.regulatory_compliance.get("required_documents", []):
                    if doc not in entity.properties.get("documents", []):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Missing required regulatory document: {doc}",
                            affected_fields=["documents"],
                            suggested_corrections=[{
                                "field": "documents",
                                "action": "add",
                                "description": f"Add the required regulatory document {doc}"
                            }]
                        ))

        # Calculate overall confidence score
        confidence_score = 1.0
        if results:
            error_weight = 0.7
            warning_weight = 0.3
            error_count = len([r for r in results if r.level == ValidationLevel.ERROR])
            warning_count = len([r for r in results if r.level == ValidationLevel.WARNING])
            total_count = len(results)
            
            if total_count > 0:
                confidence_score = 1.0 - (
                    (error_count * error_weight + warning_count * warning_weight) / total_count
                )

        validation_duration = (datetime.utcnow() - validation_start).total_seconds()

        return ValidationReport(
            entity_id=entity.id,
            results=results,
            overall_status=ValidationLevel.ERROR if any(r.level == ValidationLevel.ERROR for r in results) else ValidationLevel.WARNING if any(r.level == ValidationLevel.WARNING for r in results) else ValidationLevel.INFO,
            confidence_score=confidence_score,
            validation_duration=validation_duration
        )

    def validate_relationship(self, relationship: Relationship, source_entity: Optional[Entity] = None, target_entity: Optional[Entity] = None) -> ValidationReport:
        results = []
        confidence_scores = []
        validation_start = datetime.utcnow()

        # Get applicable rules
        applicable_rules = [
            rule for rule in self.rules.values()
            if isinstance(rule, RelationshipValidationRule) and rule.relationship_type == relationship.type
        ]

        for rule in applicable_rules:
            if not rule.enabled:
                continue

            # Validate required properties
            for prop in rule.required_properties:
                if prop not in relationship.properties:
                    results.append(ValidationResult(
                        rule_name=rule.name,
                        level=ValidationLevel.ERROR,
                        message=f"Missing required property: {prop}",
                        affected_fields=[prop],
                        suggested_corrections=[{
                            "field": prop,
                            "action": "add",
                            "description": f"Add the required property {prop}"
                        }]
                    ))

            # Validate property patterns
            for prop, pattern in rule.property_patterns.items():
                if prop in relationship.properties:
                    if not re.match(pattern, str(relationship.properties[prop])):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Property {prop} does not match required pattern",
                            affected_fields=[prop],
                            suggested_corrections=[{
                                "field": prop,
                                "action": "format",
                                "description": f"Format {prop} according to pattern: {pattern}"
                            }]
                        ))

            # Validate property ranges
            for prop, (min_val, max_val) in rule.property_ranges.items():
                if prop in relationship.properties:
                    try:
                        value = float(relationship.properties[prop])
                        if value < min_val or value > max_val:
                            results.append(ValidationResult(
                                rule_name=rule.name,
                                level=ValidationLevel.ERROR,
                                message=f"Property {prop} value {value} is outside allowed range [{min_val}, {max_val}]",
                                affected_fields=[prop],
                                suggested_corrections=[{
                                    "field": prop,
                                    "action": "adjust",
                                    "description": f"Adjust {prop} to be within range [{min_val}, {max_val}]"
                                }]
                            ))
                    except (ValueError, TypeError):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Property {prop} must be a numeric value",
                            affected_fields=[prop],
                            suggested_corrections=[{
                                "field": prop,
                                "action": "convert",
                                "description": f"Convert {prop} to a numeric value"
                            }]
                        ))

            # Validate temporal constraints
            if rule.temporal_constraints:
                for date_field, requirement in rule.temporal_constraints.items():
                    if requirement == "required" and date_field not in relationship.properties:
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Missing required date field: {date_field}",
                            affected_fields=[date_field],
                            suggested_corrections=[{
                                "field": date_field,
                                "action": "add",
                                "description": f"Add the required date field {date_field}"
                            }]
                        ))

            # Validate financial constraints
            if rule.financial_constraints:
                for metric in rule.financial_constraints.get("required_metrics", []):
                    if metric not in relationship.properties:
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Missing required financial metric: {metric}",
                            affected_fields=[metric],
                            suggested_corrections=[{
                                "field": metric,
                                "action": "add",
                                "description": f"Add the required financial metric {metric}"
                            }]
                        ))

                for metric, (min_val, max_val) in rule.financial_constraints.get("metric_ranges", {}).items():
                    if metric in relationship.properties:
                        try:
                            value = float(relationship.properties[metric])
                            if value < min_val or value > max_val:
                                results.append(ValidationResult(
                                    rule_name=rule.name,
                                    level=ValidationLevel.ERROR,
                                    message=f"Financial metric {metric} value {value} is outside allowed range [{min_val}, {max_val}]",
                                    affected_fields=[metric],
                                    suggested_corrections=[{
                                        "field": metric,
                                        "action": "adjust",
                                        "description": f"Adjust {metric} to be within range [{min_val}, {max_val}]"
                                    }]
                                ))
                        except (ValueError, TypeError):
                            results.append(ValidationResult(
                                rule_name=rule.name,
                                level=ValidationLevel.ERROR,
                                message=f"Financial metric {metric} must be a numeric value",
                                affected_fields=[metric],
                                suggested_corrections=[{
                                    "field": metric,
                                    "action": "convert",
                                    "description": f"Convert {metric} to a numeric value"
                                }]
                            ))

            # Validate regulatory compliance
            if rule.regulatory_compliance:
                for doc in rule.regulatory_compliance.get("required_documents", []):
                    if doc not in relationship.properties.get("documents", []):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Missing required regulatory document: {doc}",
                            affected_fields=["documents"],
                            suggested_corrections=[{
                                "field": "documents",
                                "action": "add",
                                "description": f"Add the required regulatory document {doc}"
                            }]
                        ))

        # Calculate overall confidence score
        confidence_score = 1.0
        if results:
            error_weight = 0.7
            warning_weight = 0.3
            error_count = len([r for r in results if r.level == ValidationLevel.ERROR])
            warning_count = len([r for r in results if r.level == ValidationLevel.WARNING])
            total_count = len(results)
            
            if total_count > 0:
                confidence_score = 1.0 - (
                    (error_count * error_weight + warning_count * warning_weight) / total_count
                )

        validation_duration = (datetime.utcnow() - validation_start).total_seconds()

        return ValidationReport(
            relationship_id=relationship.id,
            results=results,
            overall_status=ValidationLevel.ERROR if any(r.level == ValidationLevel.ERROR for r in results) else ValidationLevel.WARNING if any(r.level == ValidationLevel.WARNING for r in results) else ValidationLevel.INFO,
            confidence_score=confidence_score,
            validation_duration=validation_duration
        )

    def validate_financial_entity(self, entity: Entity, domain: FinancialDomain) -> ValidationReport:
        """Validate a financial entity against domain-specific rules"""
        results = []
        confidence_scores = []
        validation_start = datetime.utcnow()

        # Get applicable rules
        applicable_rules = [
            rule for rule in self.rules.values()
            if isinstance(rule, FinancialValidationRule) 
            and rule.entity_type == entity.type 
            and rule.domain == domain
        ]

        for rule in applicable_rules:
            if not rule.enabled:
                continue

            # Validate required fields
            for field in rule.required_fields:
                if field not in entity.properties:
                    results.append(ValidationResult(
                        rule_name=rule.name,
                        level=ValidationLevel.ERROR,
                        message=f"Missing required field: {field}",
                        affected_fields=[field],
                        suggested_corrections=[{
                            "field": field,
                            "action": "add",
                            "description": f"Add the required field {field}"
                        }]
                    ))

            # Validate field patterns
            for field, pattern in rule.field_patterns.items():
                if field in entity.properties:
                    if not re.match(pattern, str(entity.properties[field])):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Field {field} does not match required pattern",
                            affected_fields=[field],
                            suggested_corrections=[{
                                "field": field,
                                "action": "format",
                                "description": f"Format {field} according to pattern: {pattern}"
                            }]
                        ))

            # Validate financial constraints
            if rule.financial_constraints:
                for metric in rule.financial_constraints.get("required_metrics", []):
                    if metric not in entity.properties:
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Missing required financial metric: {metric}",
                            affected_fields=[metric],
                            suggested_corrections=[{
                                "field": metric,
                                "action": "add",
                                "description": f"Add the required financial metric {metric}"
                            }]
                        ))

                for metric, (min_val, max_val) in rule.financial_constraints.get("metric_ranges", {}).items():
                    if metric in entity.properties:
                        try:
                            value = float(entity.properties[metric])
                            if value < min_val or value > max_val:
                                results.append(ValidationResult(
                                    rule_name=rule.name,
                                    level=ValidationLevel.ERROR,
                                    message=f"Financial metric {metric} value {value} is outside allowed range [{min_val}, {max_val}]",
                                    affected_fields=[metric],
                                    suggested_corrections=[{
                                        "field": metric,
                                        "action": "adjust",
                                        "description": f"Adjust {metric} to be within range [{min_val}, {max_val}]"
                                    }]
                                ))
                        except (ValueError, TypeError):
                            results.append(ValidationResult(
                                rule_name=rule.name,
                                level=ValidationLevel.ERROR,
                                message=f"Financial metric {metric} must be a numeric value",
                                affected_fields=[metric],
                                suggested_corrections=[{
                                    "field": metric,
                                    "action": "convert",
                                    "description": f"Convert {metric} to a numeric value"
                                }]
                            ))

            # Validate regulatory compliance
            if rule.regulatory_framework and rule.compliance_requirements:
                for requirement in rule.compliance_requirements:
                    if requirement not in entity.properties.get("compliance_status", {}):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Missing compliance requirement: {requirement}",
                            affected_fields=["compliance_status"],
                            suggested_corrections=[{
                                "field": "compliance_status",
                                "action": "add",
                                "description": f"Add compliance requirement {requirement}"
                            }]
                        ))

            # Validate risk factors
            if rule.risk_factors:
                for risk_factor, required in rule.risk_factors.items():
                    if required and risk_factor not in entity.properties.get("risk_assessment", {}):
                        results.append(ValidationResult(
                            rule_name=rule.name,
                            level=ValidationLevel.ERROR,
                            message=f"Missing required risk factor: {risk_factor}",
                            affected_fields=["risk_assessment"],
                            suggested_corrections=[{
                                "field": "risk_assessment",
                                "action": "add",
                                "description": f"Add risk factor {risk_factor}"
                            }]
                        ))

        # Calculate overall confidence score
        confidence_score = 1.0
        if results:
            error_weight = 0.7
            warning_weight = 0.3
            error_count = len([r for r in results if r.level == ValidationLevel.ERROR])
            warning_count = len([r for r in results if r.level == ValidationLevel.WARNING])
            total_count = len(results)
            
            if total_count > 0:
                confidence_score = 1.0 - (
                    (error_count * error_weight + warning_count * warning_weight) / total_count
                )

        validation_duration = (datetime.utcnow() - validation_start).total_seconds()

        return ValidationReport(
            entity_id=entity.id,
            results=results,
            overall_status=ValidationLevel.ERROR if any(r.level == ValidationLevel.ERROR for r in results) else ValidationLevel.WARNING if any(r.level == ValidationLevel.WARNING for r in results) else ValidationLevel.INFO,
            confidence_score=confidence_score,
            validation_duration=validation_duration
        ) 