"""
Flask web application for BSD Document Generator
"""
from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
import tempfile
import json
import uuid
from pathlib import Path
import sys
from typing import Dict, Any, Callable, Optional

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.bsd_mapping import req_separation, get_bsd_summary
from src.llm import LLM
from src.app import generate_bsd_document, format_function_name

# Configure Flask to use frontend folder
app = Flask(
    __name__,
    template_folder=str(project_root / 'frontend' / 'templates'),
    static_folder=str(project_root / 'frontend' / 'static')
)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Store progress for each session
progress_store: Dict[str, Dict[str, Any]] = {}


def get_session_id() -> str:
    """Get or create session ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


def update_progress(session_id: str, stage: str, message: str, progress: int = None):
    """Update progress for a session"""
    if session_id not in progress_store:
        progress_store[session_id] = {
            'current_stage': stage,
            'message': message,
            'progress': 0,
            'stages': []
        }
    
    progress_store[session_id]['current_stage'] = stage
    progress_store[session_id]['message'] = message
    if progress is not None:
        progress_store[session_id]['progress'] = progress


def generate_with_progress(bsd_groups, session_id: str):
    """Generate BSD documents with progress tracking"""
    try:
        # Import required functions first
        from src.app import (
            extract_requirement_descriptions,
            generate_placeholder_content,
            get_requirements_by_function,
            format_function_name,
            extract_non_functional_requirements
        )
        from src.doc_editor import replace_placeholders
        from src.prompts import PROMPTS
        
        # Initialize LLM
        update_progress(session_id, 'initializing', 'Initializing LLM...', 2)
        llm = LLM()
        
        total_bsds = len(bsd_groups)
        generated_docs = []
        
        # Store function list for frontend checklist
        all_functions = []
        for bsd_group in bsd_groups:
            for func_name in bsd_group.get('unique_functions', []):
                formatted_name = format_function_name(func_name)
                if formatted_name not in all_functions:
                    all_functions.append(formatted_name)
        
        # Store functions in progress store for frontend
        if session_id not in progress_store:
            progress_store[session_id] = {}
        progress_store[session_id]['functions'] = all_functions
        
        # Calculate total steps for progress
        total_steps = 0
        for bsd_group in bsd_groups:
            # 1 step for overview, 2 steps per function (summary + implementation), 1 for assembly
            total_steps += 2 + (len(bsd_group.get('unique_functions', [])) * 2) + 1
        
        current_step = 0
        
        for idx, bsd_group in enumerate(bsd_groups):
            bsd_num = bsd_group['bsd_number']
            bsd_id = bsd_group['bsd_id']
            unique_functions = bsd_group.get('unique_functions', [])
            
            # Business Solution Overview
            current_step += 1
            progress = int((current_step / total_steps) * 90)  # 90% for generation, 10% for completion
            update_progress(
                session_id,
                'bsd_overview',
                f'BSD #{bsd_num} ({bsd_id}): Generating business solution overview...',
                progress
            )
            requirements_df = bsd_group['requirements_df']
            requirement_descriptions = extract_requirement_descriptions(requirements_df)
            
            placeholders = {}
            placeholders['business_solution_overview'] = generate_placeholder_content(
                llm=llm,
                placeholder_name="business_solution_overview",
                prompt_template=PROMPTS.get("business_solution_overview"),
                requirement_descriptions=requirement_descriptions,
                bsd_info=bsd_group
            )
            
            # Generate function contents
            function_contents = []
            for func_idx, function_name in enumerate(unique_functions):
                formatted_function_name = format_function_name(function_name)
                
                # Function Summary - use function-specific stage ID
                current_step += 1
                progress = int((current_step / total_steps) * 90)
                stage_id = f'function_summary_{formatted_function_name}'
                update_progress(
                    session_id,
                    stage_id,
                    f'BSD #{bsd_num}: Generating summary for "{formatted_function_name}" ({func_idx + 1}/{len(unique_functions)})...',
                    progress
                )
                
                func_requirements = get_requirements_by_function(requirements_df, function_name)
                func_requirements = func_requirements[
                    func_requirements['Requirement type'] == 'Functional'
                ].copy()
                
                if not func_requirements.empty:
                    func_requirements_aggregate = extract_requirement_descriptions(func_requirements)
                    
                    function_summary = generate_placeholder_content(
                        llm=llm,
                        placeholder_name="function_summary",
                        prompt_template=PROMPTS.get("function_summary"),
                        requirement_descriptions=func_requirements_aggregate,
                        bsd_info=bsd_group
                    )
                    
                    # Function Implementation - use function-specific stage ID
                    current_step += 1
                    progress = int((current_step / total_steps) * 90)
                    stage_id = f'function_implementation_{formatted_function_name}'
                    update_progress(
                        session_id,
                        stage_id,
                        f'BSD #{bsd_num}: Generating implementation for "{formatted_function_name}" ({func_idx + 1}/{len(unique_functions)})...',
                        progress
                    )
                    
                    function_implementation = generate_placeholder_content(
                        llm=llm,
                        placeholder_name="function_implementation",
                        prompt_template=PROMPTS.get("function_implementation"),
                        requirement_descriptions=func_requirements_aggregate,
                        bsd_info=bsd_group
                    )
                    
                    function_contents.append({
                        'function_name': formatted_function_name,
                        'summary': function_summary,
                        'implementation': function_implementation,
                        'requirement_count': len(func_requirements)
                    })
            
            placeholders['function_contents'] = function_contents
            
            # Extract non-functional requirements
            placeholders['non_functional_requirements'] = extract_non_functional_requirements(requirements_df)
            
            # Document Assembly
            current_step += 1
            progress = int((current_step / total_steps) * 90)
            update_progress(
                session_id,
                'document_assembly',
                f'BSD #{bsd_num} ({bsd_id}): Assembling document ({idx + 1}/{total_bsds})...',
                progress
            )
            
            output_filename = bsd_group.get('output_filename', f"BSD_{bsd_group['bsd_number']}.docx")
            output_path = replace_placeholders(
                placeholders=placeholders,
                output_filename=output_filename
            )
            
            generated_docs.append({
                'bsd_number': bsd_num,
                'bsd_id': bsd_id,
                'filename': output_path.name,
                'path': str(output_path)
            })
        
        update_progress(session_id, 'complete', 'All documents generated successfully!', 100)
        
        return {
            'success': True,
            'documents': generated_docs,
            'total': len(generated_docs)
        }
        
    except Exception as e:
        import traceback
        error_msg = f'Error: {str(e)}\n{traceback.format_exc()}'
        update_progress(session_id, 'error', error_msg, None)
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and analyze requirements"""
    session_id = get_session_id()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file extension
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in ['.xlsm', '.xlsx', '.csv']:
        return jsonify({'error': 'Unsupported file format. Please upload .xlsm, .xlsx, or .csv'}), 400
    
    # Save uploaded file temporarily
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
    file.save(temp_path)
    
    try:
        update_progress(session_id, 'analyzing', 'Analyzing requirements file...', 0)
        
        # Analyze requirements
        bsd_groups = req_separation(temp_path)
        summary_df = get_bsd_summary(bsd_groups)
        
        # Store file path and metadata in session for later generation
        # Note: Can't store DataFrames in session, so we'll re-read the file
        session['temp_file_path'] = temp_path
        session['bsd_count'] = len(bsd_groups)
        session['bsd_metadata'] = [
            {
                'bsd_number': group['bsd_number'],
                'bsd_id': group['bsd_id'],
                'output_filename': group.get('output_filename', f"BSD_{group['bsd_number']}.docx")
            }
            for group in bsd_groups
        ]
        
        # Convert summary to dict
        summary_dict = summary_df.to_dict('records')
        
        update_progress(session_id, 'analyzed', f'Found {len(bsd_groups)} BSD(s)', 0)
        
        return jsonify({
            'success': True,
            'bsd_count': len(bsd_groups),
            'summary': summary_dict,
            'bsd_groups': [
                {
                    'bsd_number': group['bsd_number'],
                    'bsd_id': group['bsd_id'],
                    'sales_product': group.get('sales_product', 'N/A'),
                    'domain': group.get('domain', 'N/A'),
                    'requirement_count': group.get('requirement_count', 0),
                    'unique_functions': group.get('unique_functions', [])
                }
                for group in bsd_groups
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate_documents():
    """Generate BSD documents"""
    session_id = get_session_id()
    
    if 'temp_file_path' not in session:
        return jsonify({'error': 'No requirements analyzed. Please upload a file first.'}), 400
    
    # Re-read BSD groups from file (can't store DataFrames in session)
    temp_file_path = session['temp_file_path']
    try:
        bsd_groups = req_separation(temp_file_path)
    except Exception as e:
        return jsonify({'error': f'Error reading requirements file: {str(e)}'}), 500
    
    # Start generation (synchronous for now)
    # In production, use Celery or threading for async processing
    result = generate_with_progress(bsd_groups, session_id)
    
    if result['success']:
        # Store generated documents in session
        session['generated_docs'] = result['documents']
    
    return jsonify(result)


@app.route('/api/progress')
def get_progress():
    """Get current progress for the session"""
    session_id = get_session_id()
    
    if session_id not in progress_store:
        return jsonify({
            'stage': 'idle',
            'message': 'No operation in progress',
            'progress': 0,
            'functions': []
        })
    
    progress_data = progress_store[session_id]
    return jsonify({
        'stage': progress_data['current_stage'],
        'message': progress_data['message'],
        'progress': progress_data.get('progress', 0),
        'functions': progress_data.get('functions', [])
    })


@app.route('/api/download/<filename>')
def download_file(filename):
    """Download generated document"""
    session_id = get_session_id()
    
    if 'generated_docs' not in session:
        return jsonify({'error': 'No documents available'}), 404
    
    # Find the document
    for doc in session['generated_docs']:
        if doc['filename'] == filename:
            file_path = Path(doc['path'])
            if file_path.exists():
                return send_file(
                    str(file_path),
                    as_attachment=True,
                    download_name=filename
                )
    
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/clear', methods=['POST'])
def clear_session():
    """Clear session data"""
    session_id = get_session_id()
    
    # Clean up temp files
    if 'temp_file_path' in session:
        temp_path = session['temp_file_path']
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    # Clear session
    session.clear()
    
    # Clear progress
    if session_id in progress_store:
        del progress_store[session_id]
    
    return jsonify({'success': True})


if __name__ == '__main__':
    # Use port 5001 to avoid conflict with macOS AirPlay Receiver (port 5000)
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)

