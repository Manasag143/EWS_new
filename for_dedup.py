from openai import AzureOpenAI

def deduplicate_high_risk_flags(high_risk_flags, api_key, azure_endpoint, api_version, deployment_name="gpt-4.1"):
    
    client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version
    )
    
    # Format input flags
    flags_text = ""
    for i, flag in enumerate(high_risk_flags, 1):
        flags_text += f"{i}. {flag}\n"
    
   
    prompt = f"""You are an experienced financial analyst for identify and eliminate duplicate high risk red flags.
        You excel at recognizing when multiple high risk flags describe the same underlying financial issue, even when worded differently, and consolidating them into single.
 
Rules:
- Remove flags about the same financial issue
- one financial value cannot be part of multiple red flags
- Preserve all numbers and percentages
- Preserve all qualitative issues
- Number the final deduplicated flags
- flags should have 1-2 sentences
- Do not lose data for qualitative issues
- only mention original quotes in filtered list of red flags, no explanatory tone
- filter, consolidate aggressively
 
Input Red Flags:
{high_risk_flags}
 
OUTPUT FORMAT:
1. [First deduplicated flag]
2. [Second deduplicated flag]
etc.
 
Review:-
1. Only output the flags, no explanation needed.
2. Ensure same financial value is NOT repeatpresent in multiple flag.
3. Ensure agrressive deduplication with above rules so number of red flags are significantly less.
 
"""

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return response.choices[0].message.content

# Usage
high_risk_flags = [
"""•	Net debt stood at INR 1,374 crores as of December 31, 2022, with management anticipating a further increase in Q4 FY23 by INR 200-300 crores to close existing projects and meet overhead requirements.
•	Borrowings during the quarter are expected to increase by INR 250-300 crores to meet project closure obligations; no equity fundraising is planned.
•	Net worth as of December 31, 2022 was INR 218 crores; cash and cash equivalents were approximately INR 181 crores.
•	Negative working capital position of INR 140 crores as of December 31, 2022, improved from negative INR 272 crores as of September 30, 2022.
•	Related party receivables were approximately INR 11 crores, net of INR 207 crores repayable to the related party for the Waste to Energy project advance.
•	Advances and performance bank guarantees encashed by four customers amounted to INR 588 crores; INR 350 crores have been refunded for two projects, with discussions ongoing for the balance.
•	Overheads of almost INR 90 crores required payment during the period.
•	Average borrowing cost on the INR 1,374 crore debt is between 9.5% and 9.7%.
•	Company articles prohibit loans to promoters; AGM resolution only facilitated return of the OLD HALL advance in the form of a loan, but no such loan has been given.
•	Revenue for 9MFY23 decreased by 51% year-on-year due to lower contribution from ongoing EPC projects.
•	Gross margins remained suppressed, primarily due to international EPC projects.
•	Net loss for the quarter declined to INR 99 crores, compared to INR 299 crores in the previous quarter and INR 429 crores in the same quarter last year.
•	EBITDA is not expected to be positive in Q4 FY23 due to limited margin in balance projects, with approximately INR 90 crores of overheads and INR 30 crores of interest offsetting operating results.
•	Losses on ongoing projects have been accounted for; unexecuted order value (UOV) is about INR 2,700 crores, with no profit/no loss projects expected to have gross margins between 10% and 11%. Gross margins are expected to normalize by Q1 FY24.
•	Legacy jobs in the order book total approximately INR 450 crores, expected to be completed mostly by Q4 FY23 or with slight overflow into FY24.
•	O&M gross margins improved to 6.7% in Q3 FY23 from negative 13% in Q2 FY23, but remain impacted by delayed revenue recognition due to client handover delays; normalization is expected in coming quarters.
•	All modules for old contracts have been supplied; remaining project costs are primarily subcontractor and commissioning costs, so recent price reductions do not benefit legacy projects.
•	Revenue increased by 1.7% quarter-on-quarter, driven by higher O&M segment contribution, but overall 9MFY23 revenue declined 51% year-on-year.
•	Negative working capital of INR 140 crores as of December 31, 2022, improved from negative INR 272 crores as of September 30, 2022.
•	Despite inflows from mobilization advances, promoter contributions, and client settlements, debt increased to INR 1,374 crores due to funding requirements for legacy projects and overheads.
•	Overheads of almost INR 90 crores required payment, necessitating additional borrowing to meet obligations in January-March.
•	Management expects debt to decrease from FY24 onwards, with a high possibility of significant reduction by Q4 FY24, depending on project size and execution.
•	Advances and performance bank guarantees encashed by four customers totaled INR 588 crores, with INR 350 crores refunded for two projects and ongoing discussions for the balance.
•	Company articles prohibit loans to promoters; AGM resolution only facilitated return of the OLD HALL advance in the form of a loan, but no such loan has been given due to group dues.
•	The company's ability to scale and execute new opportunities is constrained by manpower (staffing, retention, training) and working capital limitations, posing risks to capturing future growth and delivering large projects.
•	Capacity building measures are being implemented, but manpower and working capital remain limiting factors; management does not believe the company can execute INR 30,000-40,000 crores of projects per year at present and expects a gradual build-up.
•	Sterling & Wilson Renewable Energy Limited has no plans to manufacture electrolyzers; this activity is undertaken by a separate group company.
•	Advance percentages and working capital terms for the Reliance project are yet to be determined and will depend on negotiations; management expects non-zero advances and aims to maintain negative working capital, subject to agreement.
•	In the US, regulatory scrutiny on imported modules has resulted in large volumes of solar panels being detained at borders, delaying projects for major developers and pushing project timelines into 2023.
•	The US Solar Energy Industries Association forecasts only 16 gigawatts of solar capacity addition in 2023, similar to 2022, due to ongoing scrutiny, impacting industry activity and project execution.
•	Solar tariffs in India have declined steeply over the last six years.
•	Global solar module prices have declined from $0.28-$0.29 per watt peak last year to $0.23 per watt peak by end-2022, driven by increased manufacturing capacity.
•	Order inflow is expected to be lumpy, with stronger companies gaining market share and weaker players exiting.
•	Management recognizes significant market potential in India and internationally, with expectations of substantial growth in the Indian order book and robust opportunities in Europe, US, Australia, Latin America, and the Middle East, especially as module prices correct.
•	In the US, regulatory scrutiny on imported modules is expected to keep solar capacity additions flat at 16 gigawatts in 2023, with project delays due to customs detentions.
•	O&M gross margins improved to 6.7% in Q3 FY23 from negative 13% in Q2 FY23, but remain impacted by delayed revenue recognition due to clients delaying final handover; normalization is expected in coming quarters.
•	Persistent delays in revenue recognition and order conversion are caused by client handover delays, particularly affecting O&M margins; management expects normalization in coming quarters.
•	Several critical projects, including the Nigeria contract and large NTPC project, remain delayed in contractual closure or revenue recognition, preventing near-term financial improvement; management references ongoing negotiations with no concluded timelines, pushing expected financial uplift into FY24.
•	The company's ability to scale and execute new opportunities is constrained by manpower and working capital limitations, posing risks to capturing future growth and delivering large projects.
•	Capacity building measures are underway, but manpower and working capital remain limiting factors; management does not believe the company can execute INR 30,000-40,000 crores of projects per year at present and expects a gradual build-up.
"""]

result = deduplicate_high_risk_flags(
    high_risk_flags=high_risk_flags,
    api_key= "8498c",
    azure_endpoint= "https://crisil-pp-gpt.openai.azure.com",
    api_version= "2025-01-01-preview"
)

print(result)
