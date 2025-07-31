flowchart LR
    Start([START<br/>PDF Analysis<br/>Pipeline]) --> Init[Setup<br/>• Load Azure OpenAI LLM<br/>• Load PDF files<br/>• Load queries CSV<br/>• Load previous year data]
    
    Init --> Extract[Extract PDF Text<br/>• Use PyMuPDF fitz<br/>• Extract all pages<br/>• Merge into context]
    
    Extract --> Iter1[Iteration 1<br/>Initial Analysis<br/>• Identify red flags<br/>• Number sequentially<br/>• Include quotes<br/>• Add page references]
    
    Iter1 --> Iter2[Iteration 2<br/>Deduplication<br/>• Remove duplicates<br/>• Clean redundant entries<br/>• Preserve unique info]
    
    Iter2 --> Iter3[Iteration 3<br/>Categorization<br/>• Balance Sheet Issues<br/>• P&L Issues<br/>• Liquidity Issues<br/>• Management Issues<br/>• Regulatory Issues<br/>• Market Issues<br/>• Operational Issues]
    
    Iter3 --> Iter4[Iteration 4<br/>Summary<br/>• Create bullet points<br/>• Include quantitative data<br/>• Factual tone<br/>• Category-wise summaries]
    
    Iter4 --> Iter5[Iteration 5<br/>Classification<br/>• Most critical stage<br/>• Extract unique flags<br/>• Classify each flag]
    
    Iter5 --> Extract5[Extract Unique Flags<br/>• Ultra-strict deduplication<br/>• Max 8-10 flags only<br/>• Merge similar concepts<br/>• Return Python list]
    
    Extract5 --> Classify[Classify Each Flag<br/>• Check 15 criteria<br/>• Keyword matching<br/>• Threshold checking]
    
    Classify --> Keywords{Keyword Match?<br/>• debt_increase: debt rising<br/>• revenue_decline: sales fall<br/>• margin_decline: margin pressure<br/>• cash_balance: cash decline<br/>• management_issues: CEO change<br/>• + 10 more criteria}
    
    Keywords -->|No Match| Low[Low Risk<br/>• No keyword found<br/>• Default classification<br/>• Add to low_risk_flags]
    Keywords -->|Yes| Threshold{Threshold Check?<br/>• Compare vs previous year<br/>• Debt increase >=30%<br/>• Revenue decline >=25%<br/>• Margin decline >25%<br/>• Cash decline >25%}
    
    Threshold -->|No| Low
    Threshold -->|Yes| High[High Risk<br/>• Keyword match: YES<br/>• Threshold met: YES<br/>• Add to high_risk_flags]
    
    Low --> Results[Final Results<br/>• Display High Risk count<br/>• Display Low Risk count<br/>• Show detailed flag lists<br/>• Total flags processed]
    High --> Results
    
    Results --> Word[Create Word Doc<br/>• Company info title<br/>• Flag distribution table<br/>• High risk summaries<br/>• Category-wise summary<br/>• Multi-level deduplication]
    
    Word --> Save[Save Files<br/>• Pipeline results CSV<br/>• Classification results CSV<br/>• Word document<br/>• Timestamp all files]
    
    Save --> End([END<br/>Processing<br/>Complete])

    %% Styling - White background with dark text
    classDef default fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef decision fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef iteration fill:#f0f0f0,stroke:#000000,stroke-width:2px,color:#000000
    
    class Iter1,Iter2,Iter3,Iter4,Iter5 iteration
    class Keywords,Threshold decision

    %% Styling - White background with dark text
    classDef default fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef decision fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef iteration fill:#f0f0f0,stroke:#000000,stroke-width:2px,color:#000000
    
    class Iter1,Iter2,Iter3,Iter4,Iter5 iteration
    class Keywords,Threshold decision
