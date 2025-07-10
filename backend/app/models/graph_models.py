from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class EntityType(str, Enum):
    """Types of entities in the financial knowledge graph"""
    COMPANY = "Company"
    PERSON = "Person"
    FINANCIAL_METRIC = "FinancialMetric"
    CURRENCY = "Currency"
    PERCENTAGE = "Percentage"
    ACCOUNT = "Account"
    TRANSACTION = "Transaction"
    MARKET = "Market"
    INDUSTRY = "Industry"
    DATE = "Date"
    LOCATION = "Location"
    DOCUMENT = "Document"
    REGULATION = "Regulation"
    INTELLECTUAL_PROPERTY = "IntellectualProperty"
    FINANCIAL_INSTRUMENT = "FinancialInstrument"
    PORTFOLIO = "Portfolio"
    POLICY = "Policy"
    PROPERTY = "Property"
    CRYPTO_ASSET = "CryptoAsset"
    FINTECH_SERVICE = "FintechService"
    REGULATORY_REPORT = "RegulatoryReport"
    COMPLIANCE_CHECK = "ComplianceCheck"
    FUND = "Fund"
    SYSTEM = "System"

class RelationshipType(str, Enum):
    """Types of relationships in the financial knowledge graph"""
    # Ownership relationships
    OWNS = "OWNS"
    HAS_SUBSIDIARY = "HAS_SUBSIDIARY"
    HAS_JOINT_VENTURE = "HAS_JOINT_VENTURE"
    
    # Employment relationships
    WORKS_FOR = "WORKS_FOR"
    REPORTS_TO = "REPORTS_TO"
    IS_BOARD_MEMBER = "IS_BOARD_MEMBER"
    EMPLOYMENT = "EMPLOYMENT"
    
    # Financial relationships
    HAS_METRIC = "HAS_METRIC"
    HAS_REVENUE = "HAS_REVENUE"
    HAS_PROFIT = "HAS_PROFIT"
    HAS_ASSET = "HAS_ASSET"
    HAS_LIABILITY = "HAS_LIABILITY"
    HAS_INVESTMENT = "HAS_INVESTMENT"
    HAS_DEBT = "HAS_DEBT"
    HAS_EQUITY = "HAS_EQUITY"
    ISSUES = "ISSUES"
    
    # Business relationships
    ACQUIRES = "ACQUIRES"
    MERGES_WITH = "MERGES_WITH"
    JOINT_VENTURE = "JOINT_VENTURE"
    STRATEGIC_ALLIANCE = "STRATEGIC_ALLIANCE"
    COMPETES_WITH = "COMPETES_WITH"
    SUPPLIES_TO = "SUPPLIES_TO"
    CUSTOMER_OF = "CUSTOMER_OF"
    
    # Industry relationships
    OPERATES_IN = "OPERATES_IN"
    HEADQUARTERED_IN = "HEADQUARTERED_IN"
    HAS_OFFICE_IN = "HAS_OFFICE_IN"
    
    # Temporal relationships
    FOUNDED_ON = "FOUNDED_ON"
    ACQUIRED_ON = "ACQUIRED_ON"
    MERGED_ON = "MERGED_ON"
    
    # Location relationships
    LOCATED_IN = "LOCATED_IN"
    HAS_WAREHOUSE_IN = "HAS_WAREHOUSE_IN"
    HAS_RETAIL_IN = "HAS_RETAIL_IN"
    HAS_DISTRIBUTION_IN = "HAS_DISTRIBUTION_IN"
    
    # Financial metric relationships
    HAS_CURRENT_RATIO = "HAS_CURRENT_RATIO"
    HAS_QUICK_RATIO = "HAS_QUICK_RATIO"
    HAS_DEBT_TO_EQUITY = "HAS_DEBT_TO_EQUITY"
    HAS_INTEREST_COVERAGE = "HAS_INTEREST_COVERAGE"
    HAS_ASSET_TURNOVER = "HAS_ASSET_TURNOVER"
    HAS_INVENTORY_TURNOVER = "HAS_INVENTORY_TURNOVER"
    HAS_RECEIVABLES_TURNOVER = "HAS_RECEIVABLES_TURNOVER"
    HAS_PAYABLES_TURNOVER = "HAS_PAYABLES_TURNOVER"
    HAS_WORKING_CAPITAL = "HAS_WORKING_CAPITAL"
    HAS_FREE_CASH_FLOW = "HAS_FREE_CASH_FLOW"
    HAS_OPERATING_CASH_FLOW = "HAS_OPERATING_CASH_FLOW"
    HAS_INVESTING_CASH_FLOW = "HAS_INVESTING_CASH_FLOW"
    HAS_FINANCING_CASH_FLOW = "HAS_FINANCING_CASH_FLOW"
    HAS_CAPITAL_EXPENDITURE = "HAS_CAPITAL_EXPENDITURE"
    HAS_DEPRECIATION = "HAS_DEPRECIATION"
    HAS_AMORTIZATION = "HAS_AMORTIZATION"
    HAS_GOODWILL = "HAS_GOODWILL"
    HAS_INTANGIBLE_ASSETS = "HAS_INTANGIBLE_ASSETS"
    HAS_TANGIBLE_ASSETS = "HAS_TANGIBLE_ASSETS"
    HAS_FIXED_ASSETS = "HAS_FIXED_ASSETS"
    HAS_CURRENT_ASSETS = "HAS_CURRENT_ASSETS"
    HAS_NON_CURRENT_ASSETS = "HAS_NON_CURRENT_ASSETS"
    HAS_CURRENT_LIABILITIES = "HAS_CURRENT_LIABILITIES"
    HAS_NON_CURRENT_LIABILITIES = "HAS_NON_CURRENT_LIABILITIES"
    HAS_LONG_TERM_DEBT = "HAS_LONG_TERM_DEBT"
    HAS_SHORT_TERM_DEBT = "HAS_SHORT_TERM_DEBT"
    HAS_ACCOUNTS_RECEIVABLE = "HAS_ACCOUNTS_RECEIVABLE"
    HAS_ACCOUNTS_PAYABLE = "HAS_ACCOUNTS_PAYABLE"
    HAS_INVENTORY = "HAS_INVENTORY"
    HAS_PREPAID_EXPENSES = "HAS_PREPAID_EXPENSES"
    HAS_DEFERRED_REVENUE = "HAS_DEFERRED_REVENUE"
    HAS_ACCUMULATED_DEPRECIATION = "HAS_ACCUMULATED_DEPRECIATION"
    HAS_RETAINED_EARNINGS = "HAS_RETAINED_EARNINGS"
    HAS_TREASURY_STOCK = "HAS_TREASURY_STOCK"
    HAS_PREFERRED_STOCK = "HAS_PREFERRED_STOCK"
    HAS_COMMON_STOCK = "HAS_COMMON_STOCK"
    HAS_ADDITIONAL_PAID_IN_CAPITAL = "HAS_ADDITIONAL_PAID_IN_CAPITAL"
    HAS_OTHER_COMPREHENSIVE_INCOME = "HAS_OTHER_COMPREHENSIVE_INCOME"
    HAS_MINORITY_INTEREST = "HAS_MINORITY_INTEREST"
    HAS_OPERATING_INCOME = "HAS_OPERATING_INCOME"
    HAS_NON_OPERATING_INCOME = "HAS_NON_OPERATING_INCOME"
    HAS_EXTRAORDINARY_ITEMS = "HAS_EXTRAORDINARY_ITEMS"
    HAS_DISCONTINUED_OPERATIONS = "HAS_DISCONTINUED_OPERATIONS"
    HAS_TAX_EXPENSE = "HAS_TAX_EXPENSE"
    HAS_INTEREST_EXPENSE = "HAS_INTEREST_EXPENSE"
    HAS_DIVIDEND_PAYOUT = "HAS_DIVIDEND_PAYOUT"
    HAS_DIVIDEND_YIELD = "HAS_DIVIDEND_YIELD"
    HAS_EARNINGS_YIELD = "HAS_EARNINGS_YIELD"
    HAS_BOOK_VALUE = "HAS_BOOK_VALUE"
    HAS_TANGIBLE_BOOK_VALUE = "HAS_TANGIBLE_BOOK_VALUE"
    HAS_PRICE_TO_BOOK = "HAS_PRICE_TO_BOOK"
    HAS_PRICE_TO_SALES = "HAS_PRICE_TO_SALES"
    HAS_PRICE_TO_CASH_FLOW = "HAS_PRICE_TO_CASH_FLOW"
    HAS_ENTERPRISE_VALUE = "HAS_ENTERPRISE_VALUE"
    HAS_EV_TO_SALES = "HAS_EV_TO_SALES"
    HAS_EV_TO_EBITDA = "HAS_EV_TO_EBITDA"
    HAS_EV_TO_EBIT = "HAS_EV_TO_EBIT"
    HAS_NET_DEBT = "HAS_NET_DEBT"
    HAS_NET_DEBT_TO_EBITDA = "HAS_NET_DEBT_TO_EBITDA"
    HAS_CAPITAL_STRUCTURE = "HAS_CAPITAL_STRUCTURE"
    HAS_WEIGHTED_AVERAGE_COST_OF_CAPITAL = "HAS_WEIGHTED_AVERAGE_COST_OF_CAPITAL"
    HAS_BETA = "HAS_BETA"
    HAS_ALPHA = "HAS_ALPHA"
    HAS_SHARPE_RATIO = "HAS_SHARPE_RATIO"
    HAS_SORTINO_RATIO = "HAS_SORTINO_RATIO"
    HAS_INFORMATION_RATIO = "HAS_INFORMATION_RATIO"
    HAS_TREYNOR_RATIO = "HAS_TREYNOR_RATIO"
    HAS_JENSENS_ALPHA = "HAS_JENSENS_ALPHA"
    HAS_CAPM = "HAS_CAPM"
    HAS_DIVIDEND_DISCOUNT_MODEL = "HAS_DIVIDEND_DISCOUNT_MODEL"
    HAS_DCF = "HAS_DCF"
    HAS_RESIDUAL_INCOME = "HAS_RESIDUAL_INCOME"
    HAS_EVA = "HAS_EVA"
    HAS_MVA = "HAS_MVA"
    HAS_TOTAL_SHAREHOLDER_RETURN = "HAS_TOTAL_SHAREHOLDER_RETURN"
    HAS_INTERNAL_RATE_OF_RETURN = "HAS_INTERNAL_RATE_OF_RETURN"
    HAS_NET_PRESENT_VALUE = "HAS_NET_PRESENT_VALUE"
    HAS_PAYBACK_PERIOD = "HAS_PAYBACK_PERIOD"
    HAS_PROFITABILITY_INDEX = "HAS_PROFITABILITY_INDEX"
    HAS_MODIFIED_INTERNAL_RATE_OF_RETURN = "HAS_MODIFIED_INTERNAL_RATE_OF_RETURN"
    TRANSACTION = "TRANSACTION"

class Entity(BaseModel):
    """Base model for graph entities"""
    id: str = Field(..., description="Unique identifier for the entity")
    type: EntityType = Field(..., description="Type of the entity")
    name: str = Field(..., description="Name or label of the entity")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the entity")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    confidence: float = Field(default=1.0, description="Confidence score for entity recognition")
    source_document: Optional[str] = Field(None, description="Source document ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class Relationship(BaseModel):
    """Base model for graph relationships"""
    id: str = Field(..., description="Unique identifier for the relationship")
    type: RelationshipType = Field(..., description="Type of the relationship")
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the relationship")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    confidence: float = Field(default=1.0, description="Confidence score for relationship extraction")
    source_document: Optional[str] = Field(None, description="Source document ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class GraphNode(BaseModel):
    """Model for Neo4j node representation"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]

class GraphRelationship(BaseModel):
    """Model for Neo4j relationship representation"""
    id: str
    type: str
    start_node_id: str
    end_node_id: str
    properties: Dict[str, Any]

class GraphPath(BaseModel):
    """Model for Neo4j path representation"""
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]

class GraphQuery(BaseModel):
    """Model for graph query parameters"""
    query: str = Field(..., description="Cypher query string")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    limit: Optional[int] = Field(None, description="Maximum number of results")
    skip: Optional[int] = Field(0, description="Number of results to skip")

class GraphMetrics(BaseModel):
    """Model for graph metrics"""
    total_nodes: int = Field(..., description="Total number of nodes")
    total_relationships: int = Field(..., description="Total number of relationships")
    node_types: Dict[str, int] = Field(..., description="Count of nodes by type")
    relationship_types: Dict[str, int] = Field(..., description="Count of relationships by type")
    average_confidence: float = Field(..., description="Average confidence score")
    last_updated: datetime = Field(..., description="Last update timestamp") 