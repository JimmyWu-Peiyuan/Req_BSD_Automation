# Dictionary mapping placeholder names to their corresponding prompts

PROMPTS = {
    "business_solution_overview": """
Summarize all Description fields from the BSD's requirement rows into one clear, high-level paragraph. 
Your summary should outline the key workflows and core functionalities, highlight main processes, 
data handling and field definitions, cover relevant business rules, and clarify how customers interact with the system, 
including integrations and regional differences. Write this in a business-report style suitable for the 3.1 Business Solution Overview section, 

Example: 
'This chapter outlines the travel insurance workflows (Regular and with credit card comparator), detailing its functionality, step-by-step process, 
data handling, field definitions, and specific business rules. It provides clarity on how customers interact with the system, the integrations involved, 
and the differences across regions.
Note that the summary shouldn't be very long - keep your output similar to the example's length.
""",
    
    "function_summary": """
Generate a comprehensive summary for the function based on its associated requirements.

The summary should:
- Provide a high-level overview of what this function does
- Explain the purpose and business value of this function
- Highlight key capabilities and features
- Mention any important business rules or constraints
- Be written in a clear, professional business-report style, in paragraph format
- The summary should not exceeds 400 words

Example:
Each insurance product is required to have a unique code and name to ensure clear identification and differentiation within the system. Products must define specific coverage types, such as Comprehensive, Auto Liability, and Liability Coverage, to specify the scope of protection offered. Additionally, each product must support multiple plans with varying benefits and coverage limits—typically categorized as Basic, Standard, and Premium—to provide flexible options tailored to different customer needs.
""",
    
    "function_implementation": """
Generate a detailed functional description for the function by aggregating all requirement descriptions associated with this function. Present the information in a clear, step-by-step format.

The functional description should:
- Aggregate and synthesize all requirement descriptions provided for this function
- Present the functionality in a logical, step-by-step sequence
- Include all key capabilities, processes, and business rules mentioned in the requirements
- Be structured with clear numbered steps or sections
- Flow logically from one step to the next
- Be comprehensive but well-organized
- Use clear, professional business language
- The response not exceed 400 words

Format the output with:
- Clear numbered steps
- Logical flow that follows the natural sequence of the function's operations
- All relevant details from the requirement descriptions integrated smoothly

Focus on describing the complete functionality of this function based on all its associated requirements.
"""
}
