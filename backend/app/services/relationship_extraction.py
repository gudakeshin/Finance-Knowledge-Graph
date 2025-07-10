from typing import Dict, List, Any, Optional, Tuple
import spacy
from dataclasses import dataclass
import logging
from datetime import datetime
import uuid
import re
from .entity_recognition import FinancialEntity

logger = logging.getLogger(__name__)

@dataclass
class Relationship:
    id: str
    source_id: str
    target_id: str
    type: str
    confidence: float
    metadata: Dict[str, Any]

class RelationshipExtractor:
    def __init__(self):
        # Load English language model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded spaCy model")
        except OSError:
            logger.warning("Downloading spaCy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Define relationship types and their descriptions
        self.relationship_types = {
            # Ownership and Control
            "OWNS": "Ownership relationship",
            "CONTROLS": "Control relationship",
            "HAS_SUBSIDIARY": "Subsidiary relationship",
            "HAS_DIVISION": "Division relationship",
            "HAS_MAJORITY_STAKE": "Majority ownership stake",
            "HAS_MINORITY_STAKE": "Minority ownership stake",
            "HAS_VOTING_RIGHTS": "Voting rights relationship",
            "HAS_BOARD_SEAT": "Board seat relationship",
            
            # Employment and Organization
            "WORKS_FOR": "Employment relationship",
            "REPORTS_TO": "Reporting relationship",
            "MANAGES": "Management relationship",
            "BOARD_MEMBER": "Board membership",
            "ADVISOR": "Advisory relationship",
            "CONSULTANT": "Consulting relationship",
            "CONTRACTOR": "Contractor relationship",
            "FOUNDER": "Founding relationship",
            "CO_FOUNDER": "Co-founding relationship",
            "EXECUTIVE": "Executive position",
            "DIRECTOR": "Director position",
            "SHAREHOLDER": "Shareholder relationship",
            
            # Financial
            "INVESTS_IN": "Investment relationship",
            "ACQUIRES": "Acquisition relationship",
            "MERGES_WITH": "Merger relationship",
            "HAS_METRIC": "Financial metric relationship",
            "HAS_REVENUE": "Revenue relationship",
            "HAS_PROFIT": "Profit relationship",
            "HAS_ASSET": "Asset relationship",
            "HAS_LIABILITY": "Liability relationship",
            "HAS_DEBT": "Debt relationship",
            "HAS_EQUITY": "Equity relationship",
            "HAS_CASH_FLOW": "Cash flow relationship",
            "HAS_DIVIDEND": "Dividend relationship",
            "HAS_MARKET_CAP": "Market capitalization relationship",
            "HAS_SHARE_PRICE": "Share price relationship",
            "HAS_PE_RATIO": "P/E ratio relationship",
            "HAS_EV_EBITDA": "EV/EBITDA ratio relationship",
            "HAS_ROE": "Return on Equity relationship",
            "HAS_ROA": "Return on Assets relationship",
            "HAS_GROSS_MARGIN": "Gross margin relationship",
            "HAS_OPERATING_MARGIN": "Operating margin relationship",
            "HAS_NET_MARGIN": "Net margin relationship",
            
            # Business Relationships
            "PARTNERS_WITH": "Partnership relationship",
            "COMPETES_WITH": "Competition relationship",
            "SUPPLIES_TO": "Supply relationship",
            "CUSTOMER_OF": "Customer relationship",
            "DISTRIBUTES_FOR": "Distribution relationship",
            "LICENSES_TO": "Licensing relationship",
            "JOINT_VENTURE": "Joint venture relationship",
            "STRATEGIC_ALLIANCE": "Strategic alliance relationship",
            "RESEARCH_COLLABORATION": "Research collaboration",
            "TECHNOLOGY_PARTNER": "Technology partnership",
            "SERVICE_PROVIDER": "Service provider relationship",
            "VENDOR": "Vendor relationship",
            "RESELLER": "Reseller relationship",
            "FRANCHISEE": "Franchisee relationship",
            "FRANCHISOR": "Franchisor relationship",
            
            # Industry and Market
            "OPERATES_IN": "Market operation relationship",
            "BELONGS_TO": "Industry membership",
            "REGULATED_BY": "Regulatory relationship",
            "CERTIFIED_BY": "Certification relationship",
            "COMPLIES_WITH": "Compliance relationship",
            "HAS_PATENT": "Patent relationship",
            "HAS_TRADEMARK": "Trademark relationship",
            "HAS_LICENSE": "License relationship",
            "HAS_PERMIT": "Permit relationship",
            "HAS_APPROVAL": "Regulatory approval relationship",
            
            # Temporal
            "FOUNDED": "Founding relationship",
            "ACQUIRED_ON": "Acquisition date relationship",
            "LISTED_ON": "Listing date relationship",
            "DELISTED_ON": "Delisting date relationship",
            "BANKRUPT_ON": "Bankruptcy date relationship",
            "RESTRUCTURED_ON": "Restructuring date relationship",
            "SPUN_OFF_ON": "Spin-off date relationship",
            "IPO_ON": "Initial public offering date relationship",
            
            # Location
            "HEADQUARTERED_IN": "Headquarters location",
            "OPERATES_IN_REGION": "Regional operation",
            "HAS_OFFICE_IN": "Office location",
            "HAS_FACILITY_IN": "Facility location",
            "HAS_PLANT_IN": "Manufacturing plant location",
            "HAS_WAREHOUSE_IN": "Warehouse location",
            "HAS_RETAIL_IN": "Retail location",
            "HAS_DISTRIBUTION_IN": "Distribution center location",
            
            # Additional Financial Metrics
            "HAS_CURRENT_RATIO": "Current ratio relationship",
            "HAS_QUICK_RATIO": "Quick ratio relationship",
            "HAS_DEBT_TO_EQUITY": "Debt-to-equity ratio relationship",
            "HAS_INTEREST_COVERAGE": "Interest coverage ratio relationship",
            "HAS_ASSET_TURNOVER": "Asset turnover ratio relationship",
            "HAS_INVENTORY_TURNOVER": "Inventory turnover ratio relationship",
            "HAS_RECEIVABLES_TURNOVER": "Receivables turnover ratio relationship",
            "HAS_PAYABLES_TURNOVER": "Payables turnover ratio relationship",
            "HAS_WORKING_CAPITAL": "Working capital relationship",
            "HAS_FREE_CASH_FLOW": "Free cash flow relationship",
            "HAS_OPERATING_CASH_FLOW": "Operating cash flow relationship",
            "HAS_INVESTING_CASH_FLOW": "Investing cash flow relationship",
            "HAS_FINANCING_CASH_FLOW": "Financing cash flow relationship",
            "HAS_CAPITAL_EXPENDITURE": "Capital expenditure relationship",
            "HAS_DEPRECIATION": "Depreciation relationship",
            "HAS_AMORTIZATION": "Amortization relationship",
            "HAS_GOODWILL": "Goodwill relationship",
            "HAS_INTANGIBLE_ASSETS": "Intangible assets relationship",
            "HAS_TANGIBLE_ASSETS": "Tangible assets relationship",
            "HAS_FIXED_ASSETS": "Fixed assets relationship",
            "HAS_CURRENT_ASSETS": "Current assets relationship",
            "HAS_NON_CURRENT_ASSETS": "Non-current assets relationship",
            "HAS_CURRENT_LIABILITIES": "Current liabilities relationship",
            "HAS_NON_CURRENT_LIABILITIES": "Non-current liabilities relationship",
            "HAS_LONG_TERM_DEBT": "Long-term debt relationship",
            "HAS_SHORT_TERM_DEBT": "Short-term debt relationship",
            "HAS_ACCOUNTS_RECEIVABLE": "Accounts receivable relationship",
            "HAS_ACCOUNTS_PAYABLE": "Accounts payable relationship",
            "HAS_INVENTORY": "Inventory relationship",
            "HAS_PREPAID_EXPENSES": "Prepaid expenses relationship",
            "HAS_DEFERRED_REVENUE": "Deferred revenue relationship",
            "HAS_ACCUMULATED_DEPRECIATION": "Accumulated depreciation relationship",
            "HAS_RETAINED_EARNINGS": "Retained earnings relationship",
            "HAS_TREASURY_STOCK": "Treasury stock relationship",
            "HAS_PREFERRED_STOCK": "Preferred stock relationship",
            "HAS_COMMON_STOCK": "Common stock relationship",
            "HAS_ADDITIONAL_PAID_IN_CAPITAL": "Additional paid-in capital relationship",
            "HAS_OTHER_COMPREHENSIVE_INCOME": "Other comprehensive income relationship",
            "HAS_MINORITY_INTEREST": "Minority interest relationship",
            "HAS_OPERATING_INCOME": "Operating income relationship",
            "HAS_NON_OPERATING_INCOME": "Non-operating income relationship",
            "HAS_EXTRAORDINARY_ITEMS": "Extraordinary items relationship",
            "HAS_DISCONTINUED_OPERATIONS": "Discontinued operations relationship",
            "HAS_TAX_EXPENSE": "Tax expense relationship",
            "HAS_INTEREST_EXPENSE": "Interest expense relationship",
            "HAS_DIVIDEND_PAYOUT": "Dividend payout relationship",
            "HAS_DIVIDEND_YIELD": "Dividend yield relationship",
            "HAS_EARNINGS_YIELD": "Earnings yield relationship",
            "HAS_BOOK_VALUE": "Book value relationship",
            "HAS_TANGIBLE_BOOK_VALUE": "Tangible book value relationship",
            "HAS_PRICE_TO_BOOK": "Price-to-book ratio relationship",
            "HAS_PRICE_TO_SALES": "Price-to-sales ratio relationship",
            "HAS_PRICE_TO_CASH_FLOW": "Price-to-cash flow ratio relationship",
            "HAS_ENTERPRISE_VALUE": "Enterprise value relationship",
            "HAS_EV_TO_SALES": "EV-to-sales ratio relationship",
            "HAS_EV_TO_EBITDA": "EV-to-EBITDA ratio relationship",
            "HAS_EV_TO_EBIT": "EV-to-EBIT ratio relationship",
            "HAS_NET_DEBT": "Net debt relationship",
            "HAS_NET_DEBT_TO_EBITDA": "Net debt-to-EBITDA ratio relationship",
            "HAS_CAPITAL_STRUCTURE": "Capital structure relationship",
            "HAS_WEIGHTED_AVERAGE_COST_OF_CAPITAL": "WACC relationship",
            "HAS_BETA": "Beta relationship",
            "HAS_ALPHA": "Alpha relationship",
            "HAS_SHARPE_RATIO": "Sharpe ratio relationship",
            "HAS_SORTINO_RATIO": "Sortino ratio relationship",
            "HAS_INFORMATION_RATIO": "Information ratio relationship",
            "HAS_TREYNOR_RATIO": "Treynor ratio relationship",
            "HAS_JENSENS_ALPHA": "Jensen's alpha relationship",
            "HAS_CAPM": "Capital Asset Pricing Model relationship",
            "HAS_DIVIDEND_DISCOUNT_MODEL": "Dividend Discount Model relationship",
            "HAS_DCF": "Discounted Cash Flow relationship",
            "HAS_RESIDUAL_INCOME": "Residual income relationship",
            "HAS_EVA": "Economic Value Added relationship",
            "HAS_MVA": "Market Value Added relationship",
            "HAS_TOTAL_SHAREHOLDER_RETURN": "Total Shareholder Return relationship",
            "HAS_INTERNAL_RATE_OF_RETURN": "Internal Rate of Return relationship",
            "HAS_NET_PRESENT_VALUE": "Net Present Value relationship",
            "HAS_PAYBACK_PERIOD": "Payback period relationship",
            "HAS_PROFITABILITY_INDEX": "Profitability Index relationship",
            "HAS_MODIFIED_INTERNAL_RATE_OF_RETURN": "Modified Internal Rate of Return relationship"
        }
        
        # Define relationship patterns with enhanced context
        self._define_relationship_patterns()
        
        # Define entity type compatibility matrix
        self._define_entity_compatibility()
        
        # Define financial sentiment terms
        self._define_financial_sentiment_terms()
        
        # Define complex pattern matching rules
        self._define_complex_patterns()

    def _define_relationship_patterns(self):
        """Define patterns for different types of relationships with enhanced context"""
        self.patterns = {
            # Ownership and Control
            "OWNS": [
                ["owns", "acquired", "purchased", "bought", "acquires", "acquiring"],
                ["subsidiary", "division", "unit", "stake", "shares", "equity"]
            ],
            "CONTROLS": [
                ["controls", "manages", "operates", "runs", "directs"],
                ["operations", "business", "company", "entity"]
            ],
            "HAS_SUBSIDIARY": [
                ["subsidiary", "subsidiaries", "wholly-owned"],
                ["of", "under", "owned by"]
            ],
            
            # Employment and Organization
            "WORKS_FOR": [
                ["works", "employed", "hired", "joined", "staff", "employee"],
                ["at", "by", "for", "with"]
            ],
            "REPORTS_TO": [
                ["reports", "reported", "reporting", "reports directly to"],
                ["to", "under", "under the supervision of"]
            ],
            "MANAGES": [
                ["manages", "managing", "oversees", "supervises", "leads"],
                ["team", "department", "division", "group"]
            ],
            
            # Financial
            "INVESTS_IN": [
                ["invested", "investing", "investment", "funded", "financed"],
                ["in", "into", "through"]
            ],
            "HAS_METRIC": [
                ["revenue", "income", "profit", "loss", "earnings", "EBITDA", "EBIT"],
                ["of", "at", "reached", "amounting to", "totaling"]
            ],
            "HAS_REVENUE": [
                ["revenue", "sales", "turnover", "top line"],
                ["of", "at", "reached", "amounting to"]
            ],
            
            # Business Relationships
            "PARTNERS_WITH": [
                ["partnered", "partnership", "collaborated", "alliance", "joint venture"],
                ["with", "between", "alongside"]
            ],
            "COMPETES_WITH": [
                ["competes", "competitor", "competition", "rival", "market share"],
                ["with", "against", "in the market"]
            ],
            "SUPPLIES_TO": [
                ["supplies", "supplier", "vendor", "provides", "sources"],
                ["to", "for", "on behalf of"]
            ],
            
            # Industry and Market
            "OPERATES_IN": [
                ["operates", "operating", "active", "present"],
                ["in", "within", "across"]
            ],
            "BELONGS_TO": [
                ["member", "part", "belongs", "affiliated", "associated"],
                ["of", "to", "with"]
            ],
            
            # Temporal
            "FOUNDED": [
                ["founded", "established", "created", "incorporated", "started"],
                ["in", "on", "during"]
            ],
            "ACQUIRED_ON": [
                ["acquired", "purchased", "bought", "taken over"],
                ["on", "in", "during"]
            ],
            
            # Location
            "HEADQUARTERED_IN": [
                ["headquartered", "head office", "main office", "corporate office"],
                ["in", "at", "located in"]
            ],
            "HAS_OFFICE_IN": [
                ["office", "branch", "location", "presence"],
                ["in", "at", "located in"]
            ]
        }

    def _define_entity_compatibility(self):
        """Define which entity types can have which relationships"""
        self.entity_compatibility = {
            "COMPANY": {
                "OWNS": ["COMPANY", "SUBSIDIARY", "DIVISION"],
                "CONTROLS": ["COMPANY", "SUBSIDIARY", "DIVISION"],
                "HAS_SUBSIDIARY": ["SUBSIDIARY"],
                "WORKS_FOR": ["PERSON"],
                "REPORTS_TO": ["PERSON", "POSITION"],
                "INVESTS_IN": ["COMPANY", "PROJECT", "VENTURE"],
                "HAS_METRIC": ["FINANCIAL_METRIC"],
                "HAS_REVENUE": ["CURRENCY", "AMOUNT"],
                "PARTNERS_WITH": ["COMPANY", "ORGANIZATION"],
                "COMPETES_WITH": ["COMPANY"],
                "SUPPLIES_TO": ["COMPANY", "ORGANIZATION"],
                "OPERATES_IN": ["MARKET", "INDUSTRY", "REGION"],
                "BELONGS_TO": ["INDUSTRY", "ASSOCIATION"],
                "HEADQUARTERED_IN": ["LOCATION", "CITY", "COUNTRY"],
                "HAS_OFFICE_IN": ["LOCATION", "CITY", "COUNTRY"]
            },
            "PERSON": {
                "WORKS_FOR": ["COMPANY", "ORGANIZATION"],
                "REPORTS_TO": ["PERSON", "POSITION"],
                "MANAGES": ["TEAM", "DEPARTMENT", "DIVISION"],
                "BOARD_MEMBER": ["COMPANY", "ORGANIZATION"],
                "ADVISOR": ["COMPANY", "ORGANIZATION"]
            },
            "FINANCIAL_METRIC": {
                "HAS_METRIC": ["CURRENCY", "AMOUNT", "PERCENTAGE"]
            }
        }

    def _define_financial_sentiment_terms(self):
        """Define financial-specific sentiment terms"""
        self.financial_sentiment = {
            "positive": {
                "growth": ["growth", "increase", "rise", "surge", "jump", "spike", "soar", "climb"],
                "profitability": ["profit", "gain", "earnings", "income", "revenue", "margin", "return"],
                "performance": ["outperform", "exceed", "beat", "surpass", "outpace", "outstrip"],
                "strength": ["strong", "robust", "solid", "healthy", "stable", "resilient"],
                "opportunity": ["opportunity", "potential", "prospect", "upside", "promise"],
                "innovation": ["innovative", "breakthrough", "pioneering", "leading", "cutting-edge"],
                "efficiency": ["efficient", "optimized", "streamlined", "productive", "effective"],
                "market_position": ["leader", "dominant", "premium", "preferred", "trusted"],
                "financial_health": ["solvent", "liquid", "well-capitalized", "debt-free", "cash-rich"],
                "dividend": ["dividend", "yield", "payout", "distribution", "return"]
            },
            "negative": {
                "decline": ["decline", "decrease", "fall", "drop", "plunge", "dip", "slump", "tumble"],
                "loss": ["loss", "deficit", "shortfall", "write-down", "write-off", "impairment"],
                "risk": ["risk", "exposure", "vulnerability", "threat", "uncertainty", "volatility"],
                "weakness": ["weak", "fragile", "vulnerable", "exposed", "at risk"],
                "competition": ["competitive", "challenged", "pressured", "squeezed", "eroded"],
                "cost": ["costly", "expensive", "overhead", "burden", "drag"],
                "debt": ["debt", "leverage", "liability", "obligation", "burden"],
                "market_position": ["lagging", "trailing", "struggling", "challenged", "underperforming"],
                "financial_health": ["insolvent", "illiquid", "overleveraged", "distressed", "troubled"],
                "dividend": ["cut", "suspended", "reduced", "eliminated", "missed"]
            },
            "neutral": {
                "trend": ["trend", "pattern", "movement", "direction", "trajectory"],
                "change": ["change", "shift", "adjustment", "modification", "transition"],
                "comparison": ["compared", "relative", "versus", "against", "versus"],
                "forecast": ["forecast", "projection", "outlook", "guidance", "expectation"],
                "analysis": ["analysis", "assessment", "evaluation", "review", "examination"]
            }
        }

    def _define_complex_patterns(self):
        """Define complex pattern matching rules for financial relationships"""
        self.complex_patterns = {
            "financial_metric": {
                "patterns": [
                    # Basic metric pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:of|at|reached|amounting to|totaling)\s+(?P<value>\$?\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?)',
                    # Percentage pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:of|at|reached|amounting to|totaling)\s+(?P<value>\d+(?:\.\d+)?%)',
                    # Ratio pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:of|at|reached|amounting to|totaling)\s+(?P<value>\d+(?:\.\d+)?:\d+(?:\.\d+)?)',
                    # Year-over-year pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:increased|decreased|grew|declined|rose|fell)\s+(?:by|to)\s+(?P<value>\d+(?:\.\d+)?%)\s+(?:year-over-year|yoy|y\/y)',
                    # Quarter-over-quarter pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:increased|decreased|grew|declined|rose|fell)\s+(?:by|to)\s+(?P<value>\d+(?:\.\d+)?%)\s+(?:quarter-over-quarter|qoq|q\/q)',
                    # Sequential pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:increased|decreased|grew|declined|rose|fell)\s+(?:by|to)\s+(?P<value>\d+(?:\.\d+)?%)\s+(?:sequentially|seq)',
                    # Comparison pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:compared to|versus|vs\.?)\s+(?P<value>\$?\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?)',
                    # Range pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:between|from)\s+(?P<value>\$?\d+(?:,\d+)*(?:\.\d+)?)\s+(?:and|to)\s+(?P<value2>\$?\d+(?:,\d+)*(?:\.\d+)?)',
                    # Forecast pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:is expected|is projected|is forecasted|is estimated)\s+(?:to be|to reach|to amount to)\s+(?P<value>\$?\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?)',
                    # Guidance pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:guidance|outlook|forecast)\s+(?:of|at|for)\s+(?P<value>\$?\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?)'
                ],
                "extractors": {
                    "metric": lambda m: m.group("metric").strip(),
                    "value": lambda m: m.group("value").strip(),
                    "value2": lambda m: m.group("value2").strip() if "value2" in m.groupdict() else None
                }
            },
            "financial_ratio": {
                "patterns": [
                    # Basic ratio pattern
                    r'(?P<numerator>\w+(?:\s+\w+)*)\s+(?:to|per)\s+(?P<denominator>\w+(?:\s+\w+)*)\s+(?:ratio|multiple)\s+(?:of|at|reached|amounting to|totaling)\s+(?P<value>\d+(?:\.\d+)?)',
                    # Industry comparison pattern
                    r'(?P<numerator>\w+(?:\s+\w+)*)\s+(?:to|per)\s+(?P<denominator>\w+(?:\s+\w+)*)\s+(?:ratio|multiple)\s+(?:compared to|versus|vs\.?)\s+(?:industry average|peer group|competitors)\s+(?:of|at|reached|amounting to|totaling)\s+(?P<value>\d+(?:\.\d+)?)',
                    # Historical comparison pattern
                    r'(?P<numerator>\w+(?:\s+\w+)*)\s+(?:to|per)\s+(?P<denominator>\w+(?:\s+\w+)*)\s+(?:ratio|multiple)\s+(?:compared to|versus|vs\.?)\s+(?:previous year|last year|prior year)\s+(?:of|at|reached|amounting to|totaling)\s+(?P<value>\d+(?:\.\d+)?)',
                    # Trend pattern
                    r'(?P<numerator>\w+(?:\s+\w+)*)\s+(?:to|per)\s+(?P<denominator>\w+(?:\s+\w+)*)\s+(?:ratio|multiple)\s+(?:has|have)\s+(?:increased|decreased|improved|deteriorated)\s+(?:from|to)\s+(?P<value>\d+(?:\.\d+)?)\s+(?:to|from)\s+(?P<value2>\d+(?:\.\d+)?)'
                ],
                "extractors": {
                    "numerator": lambda m: m.group("numerator").strip(),
                    "denominator": lambda m: m.group("denominator").strip(),
                    "value": lambda m: m.group("value").strip(),
                    "value2": lambda m: m.group("value2").strip() if "value2" in m.groupdict() else None
                }
            },
            "financial_trend": {
                "patterns": [
                    # Growth trend pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:has|have)\s+(?:grown|increased|risen|climbed)\s+(?:by|at)\s+(?P<value>\d+(?:\.\d+)?%)\s+(?:annually|per year|yearly|yoy|y\/y)',
                    # Decline trend pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:has|have)\s+(?:declined|decreased|fallen|dropped)\s+(?:by|at)\s+(?P<value>\d+(?:\.\d+)?%)\s+(?:annually|per year|yearly|yoy|y\/y)',
                    # Compound growth pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:has|have)\s+(?:grown|increased|risen|climbed)\s+(?:at a|at an)\s+(?:compound annual growth rate|CAGR)\s+(?:of|at|reached|amounting to|totaling)\s+(?P<value>\d+(?:\.\d+)?%)',
                    # Seasonal pattern
                    r'(?P<metric>\w+(?:\s+\w+)*)\s+(?:shows|exhibits|displays)\s+(?:seasonal|cyclical)\s+(?:pattern|trend|variation)\s+(?:with|of)\s+(?P<value>\d+(?:\.\d+)?%)\s+(?:variation|fluctuation|change)'
                ],
                "extractors": {
                    "metric": lambda m: m.group("metric").strip(),
                    "value": lambda m: m.group("value").strip()
                }
            }
        }

    def _calculate_relationship_confidence(
        self,
        context: str,
        source: FinancialEntity,
        target: FinancialEntity,
        rel_type: str
    ) -> float:
        """
        Calculate confidence score for a relationship with enhanced factors
        """
        base_confidence = 0.6  # Base confidence score
        
        # 1. Entity Type Compatibility (0.2)
        if (source.type in self.entity_compatibility and 
            rel_type in self.entity_compatibility[source.type] and
            target.type in self.entity_compatibility[source.type][rel_type]):
            base_confidence += 0.2
        
        # 2. Context Length (0.1)
        if len(context) < 50:  # Shorter contexts are usually more reliable
            base_confidence += 0.1
        
        # 3. Entity Confidence (0.1)
        base_confidence += (source.confidence + target.confidence) * 0.05
        
        # 4. Pattern Match Quality (0.1)
        pattern_quality = self._calculate_pattern_quality(context, rel_type)
        base_confidence += pattern_quality * 0.1
        
        # 5. Temporal Indicators (0.1)
        if self._has_temporal_indicators(context):
            base_confidence += 0.1
        
        # 6. Negation Check (-0.3)
        if self._has_negation(context):
            base_confidence -= 0.3
        
        return min(max(base_confidence, 0.0), 1.0)  # Ensure between 0 and 1

    def _calculate_pattern_quality(self, context: str, rel_type: str) -> float:
        """Calculate quality of pattern match"""
        if rel_type not in self.patterns:
            return 0.0
        
        context_lower = context.lower()
        verb_patterns, prep_patterns = self.patterns[rel_type]
        
        # Check for exact matches
        verb_matches = sum(1 for v in verb_patterns if v in context_lower)
        prep_matches = sum(1 for p in prep_patterns if p in context_lower)
        
        # Calculate quality score
        quality = (verb_matches / len(verb_patterns)) * 0.6 + (prep_matches / len(prep_patterns)) * 0.4
        return quality

    def _has_temporal_indicators(self, context: str) -> bool:
        """Check for temporal indicators in context"""
        temporal_patterns = [
            r'\b(in|on|during|since|until|before|after)\s+\d{4}\b',
            r'\b(annual|quarterly|monthly|yearly)\b',
            r'\b(fiscal|financial)\s+year\b'
        ]
        return any(re.search(pattern, context, re.IGNORECASE) for pattern in temporal_patterns)

    def _has_negation(self, context: str) -> bool:
        """Check for negation in context"""
        negation_patterns = [
            r'\b(not|no|never|neither|nor|none|nothing|nowhere)\b',
            r'\b(doesn\'t|don\'t|didn\'t|isn\'t|aren\'t|wasn\'t|weren\'t)\b',
            r'\b(failed|declined|rejected|denied)\b'
        ]
        return any(re.search(pattern, context, re.IGNORECASE) for pattern in negation_patterns)

    def extract_relationships(
        self,
        text: str,
        entities: List[FinancialEntity],
        window_size: int = 100
    ) -> List[Relationship]:
        """
        Extract relationships between entities in the text with enhanced metadata
        """
        relationships = []
        doc = self.nlp(text)
        
        # Create a mapping of entity positions to entities
        entity_positions = {
            (entity.position["start"], entity.position["end"]): entity
            for entity in entities
        }
        
        # Process each sentence
        for sent in doc.sents:
            sent_text = sent.text
            sent_start = sent.start_char
            
            # Find entities in this sentence
            sent_entities = [
                entity for entity in entities
                if sent_start <= entity.position["start"] < sent.end_char
            ]
            
            # Skip if less than 2 entities in the sentence
            if len(sent_entities) < 2:
                continue
            
            # Look for relationships between entities
            for i, source in enumerate(sent_entities):
                for target in sent_entities[i+1:]:
                    # Check if entities are within window size
                    if abs(source.position["start"] - target.position["start"]) > window_size:
                        continue
                    
                    # Extract text between entities
                    start = min(source.position["start"], target.position["start"])
                    end = max(source.position["end"], target.position["end"])
                    context = text[start:end]
                    
                    # Find potential relationship
                    rel_type, confidence = self._find_relationship(
                        context,
                        source,
                        target
                    )
                    
                    if rel_type and confidence > 0.5:  # Only include high-confidence relationships
                        # Extract additional metadata
                        metadata = self._extract_relationship_metadata(
                            context,
                            source,
                            target,
                            rel_type,
                            doc
                        )
                        
                        relationship = Relationship(
                            id=str(uuid.uuid4()),
                            source_id=source.id,
                            target_id=target.id,
                            type=rel_type,
                            confidence=confidence,
                            metadata=metadata
                        )
                        relationships.append(relationship)
        
        return relationships

    def _extract_relationship_metadata(
        self,
        context: str,
        source: FinancialEntity,
        target: FinancialEntity,
        rel_type: str,
        doc: spacy.tokens.Doc
    ) -> Dict[str, Any]:
        """Extract rich metadata for relationships with enhanced financial analysis"""
        metadata = {
            "context": context,
            "detected_at": datetime.now().isoformat(),
            "source_type": source.type,
            "target_type": target.type,
            "source_text": source.text,
            "target_text": target.text,
            "sentence": next((sent.text for sent in doc.sents 
                            if sent.start_char <= source.position["start"] 
                            and sent.end_char >= target.position["end"]), ""),
            "temporal_indicators": self._extract_temporal_indicators(context),
            "quantitative_indicators": self._extract_quantitative_indicators(context),
            "sentiment": self._analyze_sentiment(context),
            "certainty": self._analyze_certainty(context)
        }
        
        # Add type-specific metadata
        if rel_type in ["HAS_METRIC", "HAS_REVENUE", "HAS_PROFIT", "HAS_ASSET", "HAS_LIABILITY"]:
            metadata["financial_details"] = self._extract_financial_details(context)
            metadata["financial_metrics"] = self._extract_financial_metrics(context)
            metadata["financial_ratios"] = self._extract_financial_ratios(context)
            metadata["financial_trends"] = self._extract_financial_trends(context)
        elif rel_type in ["ACQUIRES", "MERGES_WITH", "JOINT_VENTURE", "STRATEGIC_ALLIANCE"]:
            metadata["transaction_details"] = self._extract_transaction_details(context)
            metadata["valuation_details"] = self._extract_valuation_details(context)
            metadata["synergy_details"] = self._extract_synergy_details(context)
        elif rel_type in ["OPERATES_IN", "HEADQUARTERED_IN", "HAS_OFFICE_IN"]:
            metadata["location_details"] = self._extract_location_details(context)
            metadata["geographic_details"] = self._extract_geographic_details(context)
        elif rel_type in ["HAS_PATENT", "HAS_TRADEMARK", "HAS_LICENSE"]:
            metadata["intellectual_property_details"] = self._extract_ip_details(context)
            metadata["ip_valuation_details"] = self._extract_ip_valuation_details(context)
        elif rel_type in ["REGULATED_BY", "CERTIFIED_BY", "COMPLIES_WITH"]:
            metadata["regulatory_details"] = self._extract_regulatory_details(context)
            metadata["compliance_details"] = self._extract_compliance_details(context)
        
        return metadata

    def _extract_temporal_indicators(self, context: str) -> Dict[str, Any]:
        """Extract temporal information from context"""
        return {
            "has_date": bool(re.search(r'\b\d{4}\b', context)),
            "has_time_period": bool(re.search(r'\b(annual|quarterly|monthly|yearly)\b', context)),
            "is_historical": bool(re.search(r'\b(previous|past|former|historic)\b', context)),
            "is_future": bool(re.search(r'\b(future|upcoming|planned|scheduled)\b', context))
        }

    def _extract_quantitative_indicators(self, context: str) -> Dict[str, Any]:
        """Extract quantitative information from context"""
        return {
            "has_amount": bool(re.search(r'\$\d+(?:,\d+)*(?:\.\d+)?', context)),
            "has_percentage": bool(re.search(r'\d+(?:\.\d+)?%', context)),
            "has_ratio": bool(re.search(r'\d+(?:\.\d+)?:\d+(?:\.\d+)?', context))
        }

    def _analyze_sentiment(self, context: str) -> Dict[str, Any]:
        """Analyze sentiment of the relationship context with financial focus"""
        words = set(context.lower().split())
        sentiment_scores = {
            "positive": {"count": 0, "categories": {}},
            "negative": {"count": 0, "categories": {}},
            "neutral": {"count": 0, "categories": {}}
        }
        
        # Analyze each sentiment category
        for sentiment, categories in self.financial_sentiment.items():
            for category, terms in categories.items():
                matches = words & set(terms)
                if matches:
                    sentiment_scores[sentiment]["count"] += len(matches)
                    sentiment_scores[sentiment]["categories"][category] = {
                        "count": len(matches),
                        "terms": list(matches)
                    }
        
        # Calculate overall sentiment
        total_score = (
            sentiment_scores["positive"]["count"] - 
            sentiment_scores["negative"]["count"]
        )
        
        return {
            "overall_sentiment": "positive" if total_score > 0 else "negative" if total_score < 0 else "neutral",
            "sentiment_score": total_score,
            "positive": {
                "count": sentiment_scores["positive"]["count"],
                "categories": sentiment_scores["positive"]["categories"]
            },
            "negative": {
                "count": sentiment_scores["negative"]["count"],
                "categories": sentiment_scores["negative"]["categories"]
            },
            "neutral": {
                "count": sentiment_scores["neutral"]["count"],
                "categories": sentiment_scores["neutral"]["categories"]
            }
        }

    def _analyze_certainty(self, context: str) -> Dict[str, Any]:
        """Analyze certainty level of the relationship"""
        high_certainty = {"confirmed", "certain", "definite", "established", "proven"}
        low_certainty = {"potential", "possible", "might", "may", "could", "expected"}
        
        words = set(context.lower().split())
        return {
            "is_high_certainty": bool(words & high_certainty),
            "is_low_certainty": bool(words & low_certainty),
            "certainty_words": list(words & (high_certainty | low_certainty))
        }

    def _extract_financial_details(self, context: str) -> Dict[str, Any]:
        """Extract financial-specific details with enhanced metrics"""
        return {
            "has_currency": bool(re.search(r'\$|\€|\£|\¥', context)),
            "has_amount": bool(re.search(r'\d+(?:,\d+)*(?:\.\d+)?', context)),
            "has_percentage": bool(re.search(r'\d+(?:\.\d+)?%', context)),
            "has_ratio": bool(re.search(r'\d+(?:\.\d+)?:\d+(?:\.\d+)?', context)),
            "is_growth": bool(re.search(r'\b(growth|increase|up|rise|gain|improvement)\b', context)),
            "is_decline": bool(re.search(r'\b(decline|decrease|down|fall|drop|reduction)\b', context)),
            "has_timeframe": bool(re.search(r'\b(annual|quarterly|monthly|yearly|fiscal|financial)\b', context)),
            "has_comparison": bool(re.search(r'\b(compared|versus|against|relative|previous|prior)\b', context)),
            "has_forecast": bool(re.search(r'\b(forecast|projection|outlook|guidance|expectation)\b', context)),
            "has_benchmark": bool(re.search(r'\b(benchmark|target|goal|objective|milestone)\b', context)),
            "has_risk": bool(re.search(r'\b(risk|exposure|vulnerability|uncertainty|volatility)\b', context)),
            "has_hedge": bool(re.search(r'\b(hedge|hedging|protection|mitigation|safeguard)\b', context))
        }

    def _extract_transaction_details(self, context: str) -> Dict[str, Any]:
        """Extract transaction-specific details with enhanced information"""
        return {
            "has_amount": bool(re.search(r'\$\d+(?:,\d+)*(?:\.\d+)?', context)),
            "has_date": bool(re.search(r'\b\d{4}\b', context)),
            "has_valuation": bool(re.search(r'\b(valuation|value|worth|price|cost)\b', context)),
            "has_consideration": bool(re.search(r'\b(consideration|payment|compensation|exchange)\b', context)),
            "has_structure": bool(re.search(r'\b(structure|form|type|nature|arrangement)\b', context)),
            "has_terms": bool(re.search(r'\b(terms|conditions|provisions|agreement|contract)\b', context)),
            "has_approval": bool(re.search(r'\b(approved|approval|authorized|authorization|consent)\b', context)),
            "has_closing": bool(re.search(r'\b(closing|completion|finalization|execution|consummation)\b', context)),
            "has_announcement": bool(re.search(r'\b(announced|announcement|disclosure|release|statement)\b', context)),
            "has_regulatory": bool(re.search(r'\b(regulatory|approval|clearance|consent|authorization)\b', context)),
            "has_synergy": bool(re.search(r'\b(synergy|benefit|advantage|opportunity|potential)\b', context)),
            "has_risk": bool(re.search(r'\b(risk|exposure|uncertainty|challenge|concern)\b', context))
        }

    def _extract_location_details(self, context: str) -> Dict[str, Any]:
        """Extract location-specific details"""
        return {
            "has_country": bool(re.search(r'\b(country|nation|state|province)\b', context)),
            "has_city": bool(re.search(r'\b(city|town|municipality|metro)\b', context)),
            "has_region": bool(re.search(r'\b(region|area|zone|territory)\b', context)),
            "has_address": bool(re.search(r'\b(address|street|avenue|road|boulevard)\b', context)),
            "has_coordinates": bool(re.search(r'\b(latitude|longitude|coordinates|GPS)\b', context)),
            "is_headquarters": bool(re.search(r'\b(headquarters|HQ|head office|main office)\b', context)),
            "is_branch": bool(re.search(r'\b(branch|office|location|outlet)\b', context)),
            "is_facility": bool(re.search(r'\b(facility|plant|factory|warehouse)\b', context))
        }

    def _extract_ip_details(self, context: str) -> Dict[str, Any]:
        """Extract intellectual property details"""
        return {
            "has_patent_number": bool(re.search(r'\b(patent|pat\.|pat\. no\.)\s*#?\s*[A-Z0-9-]+\b', context)),
            "has_trademark": bool(re.search(r'\b(trademark|™|®|registered mark)\b', context)),
            "has_license_number": bool(re.search(r'\b(license|lic\.|lic\. no\.)\s*#?\s*[A-Z0-9-]+\b', context)),
            "has_expiration": bool(re.search(r'\b(expires|expiration|valid until|valid through)\b', context)),
            "has_application_date": bool(re.search(r'\b(filed|applied|application date)\b', context)),
            "has_grant_date": bool(re.search(r'\b(granted|issued|grant date)\b', context)),
            "is_pending": bool(re.search(r'\b(pending|under review|in process)\b', context)),
            "is_expired": bool(re.search(r'\b(expired|lapsed|terminated)\b', context))
        }

    def _extract_regulatory_details(self, context: str) -> Dict[str, Any]:
        """Extract regulatory and compliance details"""
        return {
            "has_regulator": bool(re.search(r'\b(regulator|regulatory|authority|agency)\b', context)),
            "has_certification": bool(re.search(r'\b(certified|certification|accredited|accreditation)\b', context)),
            "has_compliance": bool(re.search(r'\b(complies|compliance|conforms|conformity)\b', context)),
            "has_standard": bool(re.search(r'\b(standard|requirement|guideline|specification)\b', context)),
            "has_inspection": bool(re.search(r'\b(inspected|inspection|audited|audit)\b', context)),
            "has_violation": bool(re.search(r'\b(violation|breach|non-compliance|infraction)\b', context)),
            "has_penalty": bool(re.search(r'\b(penalty|fine|sanction|punishment)\b', context)),
            "has_approval": bool(re.search(r'\b(approved|approval|authorized|authorization)\b', context))
        }

    def _extract_financial_metrics(self, context: str) -> Dict[str, Any]:
        """Extract detailed financial metrics using complex pattern matching"""
        metrics = {}
        for pattern in self.complex_patterns["financial_metric"]["patterns"]:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                metric = self.complex_patterns["financial_metric"]["extractors"]["metric"](match)
                value = self.complex_patterns["financial_metric"]["extractors"]["value"](match)
                value2 = self.complex_patterns["financial_metric"]["extractors"]["value2"](match)
                
                if metric not in metrics:
                    metrics[metric] = []
                
                metric_data = {
                    "value": value,
                    "type": "single" if value2 is None else "range",
                    "pattern": pattern
                }
                
                if value2 is not None:
                    metric_data["value2"] = value2
                
                metrics[metric].append(metric_data)
        
        return metrics

    def _extract_financial_ratios(self, context: str) -> Dict[str, Any]:
        """Extract financial ratios using complex pattern matching"""
        ratios = {}
        for pattern in self.complex_patterns["financial_ratio"]["patterns"]:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                numerator = self.complex_patterns["financial_ratio"]["extractors"]["numerator"](match)
                denominator = self.complex_patterns["financial_ratio"]["extractors"]["denominator"](match)
                value = self.complex_patterns["financial_ratio"]["extractors"]["value"](match)
                value2 = self.complex_patterns["financial_ratio"]["extractors"]["value2"](match)
                
                ratio_key = f"{numerator}_to_{denominator}"
                if ratio_key not in ratios:
                    ratios[ratio_key] = []
                
                ratio_data = {
                    "numerator": numerator,
                    "denominator": denominator,
                    "value": value,
                    "type": "single" if value2 is None else "range",
                    "pattern": pattern
                }
                
                if value2 is not None:
                    ratio_data["value2"] = value2
                
                ratios[ratio_key].append(ratio_data)
        
        return ratios

    def _extract_financial_trends(self, context: str) -> Dict[str, Any]:
        """Extract financial trends using complex pattern matching"""
        trends = {}
        for pattern in self.complex_patterns["financial_trend"]["patterns"]:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                metric = self.complex_patterns["financial_trend"]["extractors"]["metric"](match)
                value = self.complex_patterns["financial_trend"]["extractors"]["value"](match)
                
                if metric not in trends:
                    trends[metric] = []
                
                trend_data = {
                    "value": value,
                    "pattern": pattern
                }
                
                trends[metric].append(trend_data)
        
        return trends

    def _extract_valuation_details(self, context: str) -> Dict[str, Any]:
        """Extract detailed valuation information"""
        return {
            "has_enterprise_value": bool(re.search(r'\b(enterprise value|EV)\b', context)),
            "has_equity_value": bool(re.search(r'\b(equity value|market cap|market capitalization)\b', context)),
            "has_valuation_multiple": bool(re.search(r'\b(valuation multiple|multiple|x)\b', context)),
            "has_discount_rate": bool(re.search(r'\b(discount rate|required return|hurdle rate)\b', context)),
            "has_growth_rate": bool(re.search(r'\b(growth rate|growth projection|growth forecast)\b', context)),
            "has_terminal_value": bool(re.search(r'\b(terminal value|perpetuity value)\b', context)),
            "has_synergy_value": bool(re.search(r'\b(synergy value|synergy benefits|cost synergies)\b', context)),
            "has_premium": bool(re.search(r'\b(premium|acquisition premium|takeover premium)\b', context)),
            "has_control_premium": bool(re.search(r'\b(control premium|minority discount)\b', context)),
            "has_liquidity_discount": bool(re.search(r'\b(liquidity discount|marketability discount)\b', context))
        }

    def _extract_synergy_details(self, context: str) -> Dict[str, Any]:
        """Extract detailed synergy information"""
        return {
            "has_cost_synergies": bool(re.search(r'\b(cost synergies|cost savings|operating synergies)\b', context)),
            "has_revenue_synergies": bool(re.search(r'\b(revenue synergies|revenue growth|top-line synergies)\b', context)),
            "has_technology_synergies": bool(re.search(r'\b(technology synergies|technical synergies|R&D synergies)\b', context)),
            "has_market_synergies": bool(re.search(r'\b(market synergies|market access|distribution synergies)\b', context)),
            "has_scale_synergies": bool(re.search(r'\b(scale synergies|economies of scale|operating leverage)\b', context)),
            "has_scope_synergies": bool(re.search(r'\b(scope synergies|scope economies|diversification benefits)\b', context)),
            "has_financial_synergies": bool(re.search(r'\b(financial synergies|tax synergies|financing synergies)\b', context)),
            "has_management_synergies": bool(re.search(r'\b(management synergies|leadership synergies|talent synergies)\b', context)),
            "has_cultural_synergies": bool(re.search(r'\b(cultural synergies|cultural fit|organizational synergies)\b', context)),
            "has_strategic_synergies": bool(re.search(r'\b(strategic synergies|strategic benefits|strategic advantages)\b', context))
        }

    def _extract_geographic_details(self, context: str) -> Dict[str, Any]:
        """Extract detailed geographic information"""
        return {
            "has_continent": bool(re.search(r'\b(continent|region|area)\b', context)),
            "has_country": bool(re.search(r'\b(country|nation|state|province)\b', context)),
            "has_city": bool(re.search(r'\b(city|town|municipality|metro)\b', context)),
            "has_address": bool(re.search(r'\b(address|street|avenue|road|boulevard)\b', context)),
            "has_coordinates": bool(re.search(r'\b(latitude|longitude|coordinates|GPS)\b', context)),
            "has_timezone": bool(re.search(r'\b(timezone|time zone|UTC|GMT)\b', context)),
            "has_climate": bool(re.search(r'\b(climate|weather|temperature|precipitation)\b', context)),
            "has_population": bool(re.search(r'\b(population|inhabitants|residents|citizens)\b', context)),
            "has_economy": bool(re.search(r'\b(economy|GDP|GNP|economic indicators)\b', context)),
            "has_infrastructure": bool(re.search(r'\b(infrastructure|transportation|utilities|facilities)\b', context))
        }

    def _extract_ip_valuation_details(self, context: str) -> Dict[str, Any]:
        """Extract detailed IP valuation information"""
        return {
            "has_patent_value": bool(re.search(r'\b(patent value|patent worth|patent valuation)\b', context)),
            "has_trademark_value": bool(re.search(r'\b(trademark value|brand value|brand worth)\b', context)),
            "has_license_value": bool(re.search(r'\b(license value|royalty value|license worth)\b', context)),
            "has_royalty_rate": bool(re.search(r'\b(royalty rate|royalty percentage|license fee)\b', context)),
            "has_remaining_life": bool(re.search(r'\b(remaining life|patent term|license term)\b', context)),
            "has_technology_readiness": bool(re.search(r'\b(technology readiness|TRL|development stage)\b', context)),
            "has_market_potential": bool(re.search(r'\b(market potential|market size|addressable market)\b', context)),
            "has_competitive_advantage": bool(re.search(r'\b(competitive advantage|market position|competitive position)\b', context)),
            "has_legal_protection": bool(re.search(r'\b(legal protection|enforcement|infringement)\b', context)),
            "has_development_cost": bool(re.search(r'\b(development cost|R&D cost|research cost)\b', context))
        }

    def _extract_compliance_details(self, context: str) -> Dict[str, Any]:
        """Extract detailed compliance information"""
        return {
            "has_compliance_program": bool(re.search(r'\b(compliance program|compliance framework|compliance system)\b', context)),
            "has_risk_assessment": bool(re.search(r'\b(risk assessment|risk analysis|risk evaluation)\b', context)),
            "has_controls": bool(re.search(r'\b(controls|internal controls|control framework)\b', context)),
            "has_monitoring": bool(re.search(r'\b(monitoring|surveillance|oversight)\b', context)),
            "has_reporting": bool(re.search(r'\b(reporting|disclosure|filing)\b', context)),
            "has_training": bool(re.search(r'\b(training|education|awareness)\b', context)),
            "has_audit": bool(re.search(r'\b(audit|review|examination)\b', context)),
            "has_remediation": bool(re.search(r'\b(remediation|corrective action|improvement)\b', context)),
            "has_whistleblower": bool(re.search(r'\b(whistleblower|reporting line|hotline)\b', context)),
            "has_documentation": bool(re.search(r'\b(documentation|records|evidence)\b', context))
        }

    def _find_relationship(
        self,
        context: str,
        source: FinancialEntity,
        target: FinancialEntity
    ) -> Tuple[Optional[str], float]:
        """
        Find the most likely relationship type between two entities
        """
        best_type = None
        best_confidence = 0.0
        
        # Convert context to lowercase for matching
        context_lower = context.lower()
        
        for rel_type, patterns in self.patterns.items():
            # Check if any pattern matches
            for verb_pattern, prep_pattern in zip(patterns[0], patterns[1]):
                if verb_pattern in context_lower and prep_pattern in context_lower:
                    # Calculate confidence based on various factors
                    confidence = self._calculate_relationship_confidence(
                        context,
                        source,
                        target,
                        rel_type
                    )
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_type = rel_type
        
        return best_type, best_confidence

    def get_relationship_types(self) -> Dict[str, str]:
        """Get list of supported relationship types and their descriptions"""
        return self.relationship_types

    def get_relationship_statistics(self, relationships: List[Relationship]) -> Dict[str, Any]:
        """Get statistics about extracted relationships"""
        stats = {
            "total_relationships": len(relationships),
            "relationships_by_type": {},
            "average_confidence": 0.0,
            "entity_pairs": set()
        }
        
        if not relationships:
            return stats
        
        # Calculate statistics
        total_confidence = 0
        for rel in relationships:
            # Count by type
            stats["relationships_by_type"][rel.type] = stats["relationships_by_type"].get(rel.type, 0) + 1
            
            # Track unique entity pairs
            stats["entity_pairs"].add((rel.source_id, rel.target_id))
            
            # Sum confidence
            total_confidence += rel.confidence
        
        # Calculate average confidence
        stats["average_confidence"] = total_confidence / len(relationships)
        
        # Convert entity_pairs set to count
        stats["unique_entity_pairs"] = len(stats["entity_pairs"])
        del stats["entity_pairs"]  # Remove the set from the stats
        
        return stats 