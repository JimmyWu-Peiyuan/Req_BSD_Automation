from pathlib import Path
import json
import logging
import sys
from typing import Dict, Any, List, Optional

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


def generate_placeholder_content(
    llm: LLM,
    placeholder_name: str,
    prompt_template: str,
    requirement_descriptions: str,
    bsd_info: Dict[str, Any]
) -> Any:
    """
    Generate content for a placeholder using LLM.
    
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
        Total Requirements: {bsd_info.get('requirement_count', 0)}

        Requirement Descriptions:
        {requirement_descriptions}
        """
    
    full_prompt = f"{prompt_template}\n\n{context}"
    
    logger.info(f"Generating content for placeholder: {placeholder_name}")
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
        llm: LLM instance for generating content
        output_filename: Optional custom filename. If None, uses bsd_group['output_filename']
    
    Returns:
        Path to the generated document
    """
    logger.info(f"Processing BSD #{bsd_group['bsd_number']}: {bsd_group['sales_product']} × {bsd_group['domain']}")
    
    # Extract requirement descriptions
    requirements_df = bsd_group['requirements_df']
    requirement_descriptions = extract_requirement_descriptions(requirements_df)
    
    if not requirement_descriptions:
        logger.warning(f"No requirement descriptions found for BSD #{bsd_group['bsd_number']}")
    
    # Generate content for each placeholder
    placeholders = {}
    for placeholder_name, prompt_template in PROMPTS.items():
        content = generate_placeholder_content(
            llm=llm,
            placeholder_name=placeholder_name,
            prompt_template=prompt_template,
            requirement_descriptions=requirement_descriptions,
            bsd_info=bsd_group
        )
        placeholders[placeholder_name] = content
    
    # Determine output filename
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
    
    # Step 1: Find BSDs in requirements file
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
    
    # Step 2: Initialize LLM
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

