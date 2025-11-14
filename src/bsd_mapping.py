import pandas as pd
from pathlib import Path
from typing import List, Dict
import logging
import json

# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def req_separation(req_path: str) -> List[Dict]:
    """
    separate out the requirement list to domains based on requirements' sales product & domain

    return sample - dictionary specifying detailed bsd information, useful for downstream bsd generations:
    [
    {
        'bsd_id': 'Travel_PolicyIssuance',           # Clean identifier
        'bsd_number': 1,                             # Sequential number
        'sales_product': 'Travel',                   # Product name
        'domain': 'Policy Issuance',                 # Domain name
        'requirement_count': 25,                     # Total reqs
        'requirements_df': <DataFrame>,              # Filtered pandas DF
        'output_filename': 'BSD_Travel_Policy.docx', # Suggested filename
        'functional_count': 20,                      # F requirements
        'non_functional_count': 5                    # NF requirements
    },
    ]
    """
    # Read requirements file
    req_file = Path(req_path)
    if not req_file.exists():
        raise FileNotFoundError(f"Requirements file not found: {req_path}")
    
    # Load data based on file extension
    if req_file.suffix.lower() == '.csv':
        df = pd.read_csv(req_path)
    elif req_file.suffix.lower() in ['.xlsx', '.xlsm']:
        df = pd.read_excel(req_path, sheet_name = 1)
    else:
        raise ValueError(f"Unsupported file format: {req_file.suffix}. Use CSV or Excel.")
    
    logger.info(f"Loaded {len(df)} requirements from {req_path}")
    
    # Validate required columns
    required_cols = ['Sales product', 'Domain']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Get unique combinations of Sales Product × Domain
    bsd_combinations = df[['Sales product', 'Domain']].drop_duplicates()
    
    logger.info(f"Found {len(bsd_combinations)} unique BSD combinations (Product × Domain)")
    
    # Create BSD groups
    bsd_groups = []
    
    for idx, (_, row) in enumerate(bsd_combinations.iterrows(), start=1):
        sales_product = row['Sales product']
        domain = row['Domain']
        
        # Filter requirements for this BSD
        bsd_requirements = df[
            (df['Sales product'] == sales_product) & 
            (df['Domain'] == domain)
        ].copy()
        
        # Create clean BSD identifier (remove special chars)
        bsd_id = f"{sales_product}_{domain}".replace(' ', '').replace('-', '')
        output_filename = f"BSD_{sales_product.replace(' ', '_')}_{domain.replace(' ', '_')}.docx"
        
        bsd_group = {
            'bsd_id': bsd_id,
            'bsd_number': idx,
            'sales_product': sales_product,
            'domain': domain,
            'requirement_count': len(bsd_requirements),
            'requirements_df': bsd_requirements,
            'output_filename': output_filename,
            'functional_count': len(bsd_requirements[bsd_requirements['Requirement type'] == 'Functional']),
            'non_functional_count': len(bsd_requirements[bsd_requirements['Requirement type'] == 'Non-Functional'])
        }
        
        bsd_groups.append(bsd_group)
        
        logger.info(
            f"BSD #{idx}: {sales_product} × {domain} | "
            f"{bsd_group['requirement_count']} reqs "
            f"(F:{bsd_group['functional_count']}, NF:{bsd_group['non_functional_count']})"
        )
    
    logger.info(f"✓ Total BSDs to generate: {len(bsd_groups)}")
    
    return bsd_groups


def get_bsd_summary(bsd_groups: List[Dict]) -> pd.DataFrame:
    """
    Get a summary DataFrame of all BSD groups.
    
    Args:
        bsd_groups: Output from req_separation()
    
    Returns:
        DataFrame with summary statistics for each BSD
    """
    summary_data = []
    
    for bsd in bsd_groups:
        summary_data.append({
            'BSD #': bsd['bsd_number'],
            'Sales Product': bsd['sales_product'],
            'Domain': bsd['domain'],
            'Total Requirements': bsd['requirement_count'],
            'Functional': bsd['functional_count'],
            'Non-Functional': bsd['non_functional_count'],
            'Output File': bsd['output_filename']
        })
    
    return pd.DataFrame(summary_data)





# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Load configuration from config.json
    config_path = Path(__file__).parent.parent / "config.json"
    
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        print("Please create a config.json file in the project root.")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Get paths from config
        paths = config.get("paths", {})
        req_file = paths.get("requirements_file")
        if not req_file:
            print("Error: 'requirements_file' not found in config.json paths")
            sys.exit(1)
        
        # Convert relative path to absolute if needed
        req_path = Path(req_file)
        if not req_path.is_absolute():
            req_path = Path(__file__).parent.parent / req_path
        
        logger.info(f"Loading requirements from: {req_path}")
        
        # Separate requirements into BSD groups
        bsd_groups = req_separation(str(req_path))
        
        # Print summary
        print("\n" + "="*80)
        print("BSD GENERATION SUMMARY")
        print("="*80)
        
        summary_df = get_bsd_summary(bsd_groups)
        print(summary_df.to_string(index=False))
        
        print("\n" + "="*80)
        print(f"Total BSDs to generate: {len(bsd_groups)}")
        print("="*80 + "\n")
        
        # Example: Access specific BSD data
        if bsd_groups:
            first_bsd = bsd_groups[0]
            print(f"Example - First BSD Details:")
            print(f"  ID: {first_bsd['bsd_id']}")
            print(f"  Product: {first_bsd['sales_product']}")
            print(f"  Domain: {first_bsd['domain']}")
            print(f"  Requirements: {first_bsd['requirement_count']}")
            print(f"  Output: {first_bsd['output_filename']}")
            print(f"\n  First 3 requirement IDs:")
            for req_id in first_bsd['requirements_df']['Requirement ID'].head(3):
                print(f"    - {req_id}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config.json: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)