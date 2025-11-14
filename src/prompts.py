# Dictionary mapping placeholder names to their corresponding prompts

PROMPTS = {
    "business_solution_overview": """
Summarize all Description fields from the BSD's requirement rows into one clear, high-level paragraph. 
Your summary should outline the key workflows and core functionalities, highlight main processes, 
data handling and field definitions, cover relevant business rules, and clarify how customers interact with the system, 
including integrations and regional differences. Write this in a business-report style suitable for the 3.1 Business Solution Overview section, 
similar to the following sample:
'This chapter outlines the travel insurance workflows (Regular and with credit card comparator), detailing its functionality, step-by-step process, 
data handling, field definitions, and specific business rules. It provides clarity on how customers interact with the system, the integrations involved, 
and the differences across regions.
Note that the summary shouldn't be very long - keep your output similar to the example's length.
"""
}
