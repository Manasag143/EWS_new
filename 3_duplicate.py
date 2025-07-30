 Define strict keyword patterns for each criteria
    criteria_keywords = {
        "debt_increase": ["debt increase", "debt increased", "debt rising", "debt growth", "higher debt", "debt went up", "debt levels", "borrowing increase"],
        "provisioning": ["provision", "write-off", "write off", "writeoff", "bad debt", "impairment", "credit loss"],
        "asset_decline": ["asset decline", "asset fall", "asset decrease", "asset value down", "asset reduction", "asset impairment"],
        "receivable_days": ["receivable days", "collection period", "DSO", "days sales outstanding", "collection time"],
        "payable_days": ["payable days", "payment period", "DPO", "days payable outstanding", "payment delay"],
        "debt_ebitda": ["debt to ebitda", "debt/ebitda", "debt ebitda ratio", "leverage ratio", "debt multiple"],
        "revenue_decline": ["revenue decline", "revenue fall", "revenue decrease", "sales decline", "top line decline", "income reduction"],
        "onetime_expenses": ["one-time", "onetime", "exceptional", "extraordinary", "non-recurring", "special charges"],
        "margin_decline": ["margin decline", "margin fall", "margin pressure", "margin compression", "profitability decline", "margin squeeze"],
        "cash_balance": ["cash decline", "cash decrease", "cash balance fall", "liquidity issue", "cash shortage", "cash position"],
        "short_term_debt": ["short-term debt", "current liabilities", "working capital", "short term borrowing", "immediate obligations"],
        "management_issues": ["management change", "leadership change", "CEO", "CFO", "resignation", "departure", "management turnover"],
        "regulatory_compliance": ["regulatory", "compliance", "regulation", "regulator", "legal", "penalty", "violation", "sanctions"],
        "market_competition": ["competition", "competitive", "market share", "competitor", "market pressure", "competitive pressure"],
        "operational_disruptions": ["operational", "supply chain", "production", "manufacturing", "disruption", "operational issues"]
    }
    
    criteria_list = "\n".join([f"{i+1}. {name}: {desc}" for i, (name, desc) in enumerate(criteria_definitions.items())])
    
    # Build keyword list for prompt
    keywords_section = "\nKEYWORDS FOR EACH CRITERIA:\n"
    for criteria, keywords in criteria_keywords.items():
        keywords_section += f"  * {criteria}: {', '.join(keywords)}\n"
    
