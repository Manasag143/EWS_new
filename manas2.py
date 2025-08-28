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
    
    # Deduplication prompt
    prompt = f"""You are a financial analyst. Deduplicate the high risk flags below by merging similar ones.

RULES:
- Merge flags about the same financial issue
- Keep the most comprehensive version
- Preserve all numbers and percentages
- Number the final deduplicated flags

INPUT FLAGS:
{flags_text}

OUTPUT FORMAT:
1. [First deduplicated flag]
2. [Second deduplicated flag]
etc.

Deduplicated flags:"""

    # Call LLM
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    return response.choices[0].message.content

# Usage
high_risk_flags = [
    "Revenue declined 35% vs previous quarter",
    "Operating margins fell 40% due to cost pressures", 
    "Revenue dropped 35% in Q3 showing severe decline"
]

result = deduplicate_high_risk_flags(
    high_risk_flags=high_risk_flags,
    api_key="your_key",
    azure_endpoint="your_endpoint", 
    api_version="2025-01-01-preview"
)

print(result)
