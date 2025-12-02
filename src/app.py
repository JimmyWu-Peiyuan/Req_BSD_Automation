from pathlib import Path
import json
import logging
import sys
from typing import Dict, Any, List, Optional
import pandas as pd


# Add project root to Python path so imports work from anywhere
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.bsd_mapping import req_separation, get_bsd_summary
from src.llm import LLM
from src.doc_editor import replace_placeholders
from src.prompts import PROMPTS

# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_function_name(function_name: str) -> str:
    """
    Normalize function name for case-insensitive comparison.
    Converts to lowercase and strips whitespace.
    
    Args:
        function_name: Function name string
        
    Returns:
        Normalized function name (lowercase, stripped)
    """
    return str(function_name).strip().lower()


def format_function_name(function_name: str) -> str:
    """
    Format function name to title case (first letter of each word capitalized).
    
    Args:
        function_name: Function name string
        
    Returns:
        Title-cased function name (e.g., "Product Definition")
    """
    return str(function_name).strip().title()


def get_requirements_by_function(requirements_df, function_name: str):
    """
    Filter requirements DataFrame to get all requirements for a specific function.
    Case-insensitive matching.
    
    Args:
        requirements_df: pandas DataFrame containing requirements
        function_name: Name of the function to filter by (will be normalized for matching)
        
    Returns:
        Filtered DataFrame containing only requirements for this function
    """
    if 'Function' not in requirements_df.columns:
        logger.warning("'Function' column not found in requirements DataFrame")
        return pd.DataFrame()
    
    # Normalize the search function name
    normalized_search = normalize_function_name(function_name)
    
    # Case-insensitive comparison
    mask = requirements_df['Function'].apply(
        lambda x: normalize_function_name(x) == normalized_search if pd.notna(x) else False
    )
    
    return requirements_df[mask].copy()


def extract_requirement_descriptions(requirements_df) -> str:
    """
    Extract all Description fields from requirements DataFrame and combine into a single text.
    
    Args:
        requirements_df: pandas DataFrame containing requirements
    
    Returns:
        Combined text of all requirement descriptions
    """
    if 'Description' not in requirements_df.columns:
        logger.warning("'Description' column not found in requirements DataFrame")
        return ""
    
    descriptions = requirements_df['Description'].dropna().tolist()
    return "\n".join([f"- {desc}" for desc in descriptions if desc.strip()])


def extract_non_functional_requirements(requirements_df) -> List[Dict[str, str]]:
    """
    Extract non-functional requirements as a simple list.
    
    Args:
        requirements_df: pandas DataFrame containing requirements
        
    Returns:
        List of dictionaries with 'requirement' and 'description' keys
    """
    if 'Requirement type' not in requirements_df.columns:
        return []
    
    non_functional_reqs = requirements_df[
        requirements_df['Requirement type'] == 'Non-Functional'
    ].copy()
    
    if non_functional_reqs.empty:
        return []
    
    result = []
    for _, row in non_functional_reqs.iterrows():
        result.append({
            'requirement': str(row.get('Requirement', '')) if pd.notna(row.get('Requirement')) else '',
            'description': str(row.get('Description', '')) if pd.notna(row.get('Description')) else ''
        })
    
    return result


def generate_placeholder_content(
    llm: LLM,
    placeholder_name: str,
    prompt_template: str,
    requirement_descriptions: str,
    bsd_info: Dict[str, Any]
) -> Any:
    """
    Generate content for ONE field in the BSD document using LLM.

    Args:
        llm: LLM instance
        placeholder_name: Name of the placeholder
        prompt_template: Prompt template from PROMPTS
        requirement_descriptions: Combined text of requirement descriptions
        bsd_info: Dictionary containing BSD information (sales_product, domain, etc.)
    
    Returns:
        Generated content string
    """
    # Format the prompt with BSD context
    context = f"""
        Sales Product: {bsd_info.get('sales_product', 'N/A')}
        Domain: {bsd_info.get('domain', 'N/A')}
        Requirement Descriptions:
        {requirement_descriptions}
        """
    
    full_prompt = f"{prompt_template}\n\n{context}"
    
    try:
        content = llm.generate_response(full_prompt)
        logger.info(f"✓ Generated content for {placeholder_name} ({len(content)} characters)")
        
        return content
    except Exception as e:
        logger.error(f"Error generating content for {placeholder_name}: {e}")
        return f"[Error generating content: {str(e)}]"


def generate_bsd_document(
    bsd_group: Dict[str, Any],
    llm: LLM,
    output_filename: Optional[str] = None
) -> Path:
    """
    Generate a BSD document for a single BSD group.
    
    Args:
        bsd_group: BSD group dictionary from req_separation()
        Sample Data of bsd_group{
        'bsd_id': 'Travel_PolicyIssuance',           # Clean identifier
        'bsd_number': 1,                             # Sequential number
        'sales_product': 'Travel',                   # Product name
        'domain': 'Policy Issuance',                 # Domain name
        'requirement_count': 25,                     # Total reqs
        'requirements_df': <DataFrame>,              # Filtered pandas DF
        'output_filename': 'BSD_Travel_Policy.docx', # Suggested filename
        'functional_count': 20,                      # F requirements
        'unique_functions': ['product_definition', 'feature_set'],
        'non_functional_count': 5                    # NF requirements
        }
        llm: LLM instance for generating content
        output_filename: Optional custom filename. If None, uses bsd_group['output_filename']
    
    Returns:
        Path to the generated document
    """
    logger.info(f"Processing BSD #{bsd_group['bsd_number']}: {bsd_group['sales_product']} × {bsd_group['domain']}")
    
    # Step 1: get the information from the BSD group
    # Extract requirement descriptions
    requirements_df = bsd_group['requirements_df']

    # all contents of the requirement df, including functional & non-functional
    requirement_descriptions = extract_requirement_descriptions(requirements_df)
    if not requirement_descriptions:
        logger.warning(f"No requirement descriptions found for BSD #{bsd_group['bsd_number']}")
    
    # Initialize the placeholders dictionary
    placeholders = {}

    # generate business solution overview
    logger.info("Generating business solution overview...")
    placeholders['business_solution_overview'] = generate_placeholder_content(
        llm=llm,
        placeholder_name="business_solution_overview",
        prompt_template=PROMPTS.get("business_solution_overview"),
        requirement_descriptions=requirement_descriptions,
        bsd_info=bsd_group
    )


    # Step 2: For each unique function, generate overview and step by step implementation
    unique_functions = bsd_group.get('unique_functions', [])
    function_contents = []

    for function_name in unique_functions:
        # Format function name to title case for display
        formatted_function_name = format_function_name(function_name)
        
        logger.info(f"Generating information for {formatted_function_name} function...")
        
        # Step 2.1 filter out requirements that's only belonged to this function
        # Use original function_name for matching (case-insensitive)
        func_requirements = get_requirements_by_function(requirements_df, function_name)
        
        # Step 2.2 Filter to only Functional requirements (excludes non-functional)
        func_requirements = func_requirements[
            func_requirements['Requirement type'] == 'Functional'
        ].copy()

        if func_requirements.empty:
            logger.warning(f"No functional requirements found for function: {formatted_function_name}")
            continue

        # Step 2.3 aggregate the function requirements information
        func_requirements_aggregate = extract_requirement_descriptions(func_requirements)
        
        # Step 2.4 generate function contents
        # field 1 - function summary
        logger.info(f"Generating function summary for {formatted_function_name} ...")
        function_summary = generate_placeholder_content(
            llm=llm,
            placeholder_name="function_summary",
            prompt_template=PROMPTS.get("function_summary"),
            requirement_descriptions=func_requirements_aggregate,
            bsd_info=bsd_group
        )
        # field 2 - function implementation
        logger.info(f"Generating function implementation for {formatted_function_name} ...")
        function_implementation = generate_placeholder_content(
            llm=llm,
            placeholder_name="function_implementation",
            prompt_template=PROMPTS.get("function_implementation"),
            requirement_descriptions=func_requirements_aggregate,
            bsd_info=bsd_group
        )

        # Step 2.5 store function content (use formatted name for display)
        function_contents.append({
            'function_name': formatted_function_name,  # Title case for display
            'summary': function_summary,
            'implementation': function_implementation,
            'requirement_count': len(func_requirements)
        })
    # Add function contents to placeholders
    placeholders['function_contents'] = function_contents

    # Step 3: Extract non-functional requirements
    logger.info("Extracting non-functional requirements...")
    placeholders['non_functional_requirements'] = extract_non_functional_requirements(requirements_df)
    logger.info(f"Found {len(placeholders['non_functional_requirements'])} non-functional requirement(s)")
    
    if output_filename is None:
        output_filename = bsd_group.get('output_filename', f"BSD_{bsd_group['bsd_number']}.docx")
    
    # Generate document
    logger.info(f"Generating document: {output_filename}")
    output_path = replace_placeholders(
        placeholders=placeholders,
        output_filename=output_filename
    )
    
    logger.info(f"✓ Generated document: {output_path}")
    return output_path


def main():
    """
    Main function to orchestrate the BSD document generation process.
    """
    # Load configuration
    config_path = Path(__file__).parent.parent / "config.json"
    
    if not config_path.exists():
        logger.error(f"Config file not found at {config_path}")
        return
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    paths = config.get("paths", {})
    requirements_file = paths.get("requirements_file")
    
    if not requirements_file:
        logger.error("requirements_file not found in config.json")
        return
    
    # Convert relative path to absolute
    req_path = Path(requirements_file)
    if not req_path.is_absolute():
        req_path = Path(__file__).parent.parent / req_path
    
    logger.info("="*80)
    logger.info("BSD DOCUMENT GENERATION")
    logger.info("="*80)
    
    # Step 1: Find BSDs in requirements file (determine how many BSDs to generate)
    logger.info(f"\nStep 1: Loading requirements from {req_path}")
    try:
        bsd_groups = req_separation(str(req_path))
        logger.info(f"Found {len(bsd_groups)} BSD(s) to generate")
        
        # Print summary
        summary_df = get_bsd_summary(bsd_groups)
        print("\n" + "="*80)
        print("BSD SUMMARY")
        print("="*80)
        print(summary_df.to_string(index=False))
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error loading requirements: {e}")
        return
    
    # Step 2: Initialize LLM for content generation
    logger.info("\nStep 2: Initializing LLM")
    try:
        llm = LLM()
        logger.info("✓ LLM initialized")
    except Exception as e:
        logger.error(f"Error initializing LLM: {e}")
        return
    
    # Step 3: Generate documents for each BSD
    logger.info(f"\nStep 3: Generating {len(bsd_groups)} BSD document(s)")
    generated_docs = []
    
    # 3.1 - for each bsd, call generate_bsd_document
    for bsd_group in bsd_groups:
        try:

            output_path = generate_bsd_document(bsd_group, llm)
            generated_docs.append({
                'bsd_number': bsd_group['bsd_number'],
                'bsd_id': bsd_group['bsd_id'],
                'output_path': output_path
            })
        except Exception as e:
            logger.error(f"Error generating document for BSD #{bsd_group['bsd_number']}: {e}")
            continue
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("GENERATION COMPLETE")
    logger.info("="*80)
    logger.info(f"Successfully generated {len(generated_docs)}/{len(bsd_groups)} document(s)")
    
    for doc in generated_docs:
        logger.info(f"  BSD #{doc['bsd_number']} ({doc['bsd_id']}): {doc['output_path']}")
    
    return generated_docs


if __name__ == "__main__":
    import sys
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

