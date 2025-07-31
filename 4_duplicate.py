flowchart TD
    Start([START<br/>PDF Analysis<br/>Pipeline]) --> Init[Setup<br/>• Load Azure OpenAI LLM<br/>• Load PDF files<br/>• Load queries CSV<br/>• Load previous year data]
    
    Init --> Extract[Extract PDF Text<br/>• Use PyMuPDF fitz<br/>• Extract all pages<br/>• Merge into context]
    
    Extract --> Iter1[Iteration 1<br/>Initial Analysis<br/>• Identify red flags<br/>• Number sequentially<br/>• Include quotes<br/>• Add page references]
    
    Iter1 --> Iter2[Iteration 2<br/>Deduplication<br/>• Remove duplicates<br/>• Clean redundant entries<br/>• Preserve unique info]
    
    Iter2 --> Iter3[Iteration 3<br/>Categorization<br/>• Balance Sheet Issues<br/>• P&L Issues<br/>• Liquidity Issues<br/>• Management Issues<br/>• Regulatory Issues<br/>• Market Issues<br/>• Operational Issues]
    
    Iter3 --> Iter4[Iteration 4<br/>Summary<br/>• Create bullet points<br/>• Include quantitative data<br/>• Factual tone<br/>• Category-wise summaries]
    
    Iter4 --> ToIter5([Ready for<br/>Iteration 5])

    %% Styling - White background with dark text
    classDef default fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef iteration fill:#f0f0f0,stroke:#000000,stroke-width:2px,color:#000000
    classDef endpoint fill:#e0e0e0,stroke:#000000,stroke-width:2px,color:#000000
    
    class Iter1,Iter2,Iter3,Iter4 iteration
    class ToIter5 endpoint




flowchart TD
    FromIter4([From<br/>Iteration 4]) --> Iter5[Iteration 5<br/>Classification<br/>• Most critical stage<br/>• Extract unique flags<br/>• Classify each flag]
    
    Iter5 --> Extract5[Extract Unique Flags<br/>• Ultra-strict deduplication<br/>• Max 8-10 flags only<br/>• Merge similar concepts<br/>• Return Python list]
    
    Extract5 --> Display[Display Unique Flags<br/>• Show total count<br/>• Numbered list<br/>• Before classification]
    
    Display --> Classify[Classify Each Flag<br/>• Check 15 criteria<br/>• Keyword matching<br/>• Threshold checking]
    
    Classify --> Keywords{Keyword Match?<br/>15 Criteria Check<br/>debt_increase<br/>revenue_decline<br/>margin_decline<br/>cash_balance<br/>management_issues<br/>and 10 more}
    
    Keywords -->|No Match| Low[Low Risk<br/>• No keyword found<br/>• Default classification<br/>• Add to low_risk_flags]
    
    Keywords -->|Yes| Threshold{Threshold Check?<br/>• Compare vs previous year<br/>• Debt increase >=30%<br/>• Revenue decline >=25%<br/>• Margin decline >25%<br/>• Cash decline >25%}
    
    Threshold -->|No| Low
    Threshold -->|Yes| High[High Risk<br/>• Keyword match: YES<br/>• Threshold met: YES<br/>• Add to high_risk_flags]
    
    Low --> ToResults([To Results<br/>Generation])
    High --> ToResults

    %% Styling - White background with dark text
    classDef default fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef decision fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef iteration fill:#f0f0f0,stroke:#000000,stroke-width:2px,color:#000000
    classDef endpoint fill:#e0e0e0,stroke:#000000,stroke-width:2px,color:#000000
    classDef classification fill:#f5f5f5,stroke:#000000,stroke-width:2px,color:#000000
    
    class Iter5 iteration
    class Keywords,Threshold decision
    class FromIter4,ToResults endpoint
    class Low,High classification




flowchart TD
    FromClassification([From<br/>Classification]) --> Results[Final Results<br/>• Display High Risk count<br/>• Display Low Risk count<br/>• Show detailed flag lists<br/>• Total flags processed]
    
    Results --> CompanyInfo[Extract Company Info<br/>• Parse first page<br/>• Company name<br/>• Quarter Q1/Q2/Q3/Q4<br/>• Financial year<br/>• Format: Company-QuarterFY]
    
    CompanyInfo --> HighRiskSummary[Generate High Risk Summaries<br/>• Multi-Level Deduplication<br/>• 1. Deduplicate flags<br/>• 2. Generate summaries<br/>• 3. Remove duplicates<br/>• 4. Final doc deduplication]
    
    HighRiskSummary --> CreateWord[Create Word Document<br/>• Title: Company Info<br/>• Flag Distribution Table<br/>• High Risk Summary<br/>• Category-wise Summary<br/>• All 7 categories]
    
    CreateWord --> SaveCSV[Save CSV Files<br/>• Pipeline results CSV<br/>• Classification results CSV<br/>• Timestamp all files]
    
    SaveCSV --> SaveWord[Save Word Document<br/>• Professional formatting<br/>• Ready for review<br/>• Timestamped filename]
    
    SaveWord --> Complete[Processing Complete<br/>• Success/Failure status<br/>• Processing time<br/>• File locations<br/>• Ready for next PDF]
    
    Complete --> CheckMore{More PDFs<br/>to Process?}
    
    CheckMore -->|Yes| NextPDF[Process Next PDF<br/>• Load next file<br/>• Repeat entire pipeline<br/>• Continue batch processing]
    
    CheckMore -->|No| End([END<br/>All PDFs<br/>Processed])
    
    NextPDF --> BackToStart([Back to<br/>START])

    %% Styling - White background with dark text
    classDef default fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef decision fill:#ffffff,stroke:#000000,stroke-width:2px,color:#000000
    classDef process fill:#f0f0f0,stroke:#000000,stroke-width:2px,color:#000000
    classDef endpoint fill:#e0e0e0,stroke:#000000,stroke-width:2px,color:#000000
    classDef output fill:#f5f5f5,stroke:#000000,stroke-width:2px,color:#000000
    
    class Results,CompanyInfo,HighRiskSummary process
    class CreateWord,SaveCSV,SaveWord output
    class CheckMore decision
    class FromClassification,BackToStart,End endpoint
