from pydantic import BaseModel
from typing import List, Dict, Optional

class StockMetadata(BaseModel):
    name: str
    sector: str
    industry: str
    market_cap: int
    dividend_yield: Optional[float]
    pe_ratio: Optional[float]
    eps: Optional[float]
    beta: Optional[float]
    analyst_ratings: float
    price_targets: float
    events: str
    about_ticker: str
    
class CurrentPrice(BaseModel):
    current_price: float

class StockHistoricalData(BaseModel):
    Date: str
    Open: float
    High: float
    Low: float
    Close: float
    Volume: int
    
class NewsHeadline(BaseModel):
    number: int
    title: str
    summary: str
    pubDate: str
    conicalURL: str
    
class IncomeStatement(BaseModel):
    fiscal_date_ending: str
    reported_currency: str
    gross_profit: Optional[float]
    total_revenue: Optional[float]
    operating_income: Optional[float]
    net_income: Optional[float]
    research_and_development: Optional[float]
    operating_expense: Optional[float]
    current_assets: Optional[float]
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    shareholder_equity: Optional[float]
    cash_and_cash_equivalents: Optional[float]
    capital_expenditures: Optional[float] 
    
class BalanceSheet(BaseModel):
    fiscal_date_ending: str
    reported_currency: str
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    total_shareholder_equity: Optional[float]
    cash_and_cash_equivalents: Optional[float]
    short_term_investments: Optional[float]
    long_term_investments: Optional[float]
    property_plant_equipment: Optional[float]
    goodwill: Optional[float]
    intangible_assets: Optional[float]
    total_current_assets: Optional[float]
    total_current_liabilities: Optional[float]
    long_term_debt: Optional[float]
    short_term_debt: Optional[float]
    inventory: Optional[float]
    accounts_receivable: Optional[float]
    accounts_payable: Optional[float]
    other_current_assets: Optional[float]
    other_non_current_assets: Optional[float]
    other_current_liabilities: Optional[float]
    other_non_current_liabilities: Optional[float]
    retained_earnings: Optional[float]
    common_stock: Optional[float]
    common_stock_shares_outstanding: Optional[float]
    current_net_receivables: Optional[float]
    current_accounts_payable: Optional[float]
    deferred_revenue: Optional[float]
    current_debt: Optional[float]
    capital_lease_obligations: Optional[float]
    accumulated_depreciation_amortization_ppe: Optional[float]
    total_non_current_assets: Optional[float]
    total_non_current_liabilities: Optional[float]
    treasury_stock: Optional[float]
    investments: Optional[float]
    long_term_debt_noncurrent: Optional[float]
    short_long_term_debt_total: Optional[float]

class CashFlow(BaseModel):
    fiscal_date_ending: str
    reported_currency: str
    operating_cash_flow: Optional[float]
    payments_for_operating_activities: Optional[float]
    proceeds_from_operating_activities: Optional[float]
    change_in_operating_liabilities: Optional[float]
    change_in_operating_assets: Optional[float]
    depreciation_depletion_and_amortization: Optional[float]
    capital_expenditures: Optional[float]
    change_in_receivables: Optional[float]
    change_in_inventory: Optional[float]
    profit_loss: Optional[float]
    cash_flow_from_financing: Optional[float]
    cash_flow_from_investing: Optional[float]
    dividends_paid: Optional[float]
    change_in_cash_and_cash_equivalents: Optional[float]

class Earnings(BaseModel):
    fiscalDateEnding: str
    reportedEPS: Optional[float]
    
class SMA(BaseModel):
    date: str
    SMA: float
    
class EMA(BaseModel):
    data: str
    EMA: float    
    
class QuestionRequest(BaseModel):
    question: str
    context: str = None