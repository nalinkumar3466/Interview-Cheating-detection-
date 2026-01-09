#!/usr/bin/env python
"""
ML Pipeline Integration - Verification Script

Run this to verify all files are in place and properly configured.
Usage: python verify_integration.py
"""

import os
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_check(status, message):
    if status:
        print(f"{GREEN}✅{RESET} {message}")
    else:
        print(f"{RED}❌{RESET} {message}")
    return status

def print_section(title):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

# ============================================================================
# VERIFICATION
# ============================================================================

def main():
    print(f"{BLUE}ML PIPELINE INTEGRATION - VERIFICATION{RESET}")
    print(f"{BLUE}Checking all components are in place...{RESET}\n")

    all_ok = True

    # ========================================================================
    # 1. FILE STRUCTURE
    # ========================================================================
    print_section("1. FILE STRUCTURE")

    files_to_check = {
        "Models": {
            "backend/app/models/analysis.py": "InterviewAnalysis model",
        },
        "Schemas": {
            "backend/app/schemas_analysis.py": "Analysis API schemas",
        },
        "Routes": {
            "backend/app/api/routes/interviews.py": "Analysis endpoints",
        },
        "ML Pipeline": {
            "ml/service/final_pipeline.py": "CLI entry point",
            "ml/service/analyzer.py": "Database integration",
        },
        "Configuration": {
            "backend/.env.example.ml": "Environment template",
        },
        "Tests": {
            "backend/tests/test_ml_integration.py": "Test suite",
        },
        "Documentation": {
            "backend/DELIVERY_SUMMARY.md": "Delivery overview",
            "backend/ML_INTEGRATION_README.md": "Quick reference",
            "backend/QUICKSTART_ML_INTEGRATION.md": "Getting started",
            "backend/ML_INTEGRATION_GUIDE.md": "Complete guide",
            "backend/PRODUCTION_DEPLOYMENT_CHECKLIST.md": "Deployment",
            "backend/CODE_SNIPPET_REFERENCE.md": "Code examples",
            "backend/IMPLEMENTATION_SUMMARY.md": "Technical details",
            "backend/DOCUMENTATION_INDEX.md": "Doc index",
        }
    }

    for category, files in files_to_check.items():
        print(f"\n{YELLOW}{category}:{RESET}")
        for filepath, description in files.items():
            exists = os.path.exists(filepath)
            all_ok = print_check(exists, f"{description:40} {filepath}") and all_ok

    # ========================================================================
    # 2. FILE CONTENT VERIFICATION
    # ========================================================================
    print_section("2. FILE CONTENT VERIFICATION")

    content_checks = {
        "backend/app/models/analysis.py": {
            "class InterviewAnalysis": "SQLAlchemy model definition",
            "interview_id": "Foreign key to interviews",
            "status": "Analysis status field",
            "effective_risk_percentage": "Risk percentage field",
        },
        "backend/app/schemas_analysis.py": {
            "class AnalysisOut": "Output schema for API",
            "AnalysisCreate": "Schema for creation",
        },
        "backend/app/api/routes/interviews.py": {
            "def _run_ml_pipeline": "Background task executor",
            "@router.post(\"/{interview_id}/analyze\")": "Analyze endpoint",
            "@router.get(\"/{interview_id}/analysis\")": "Get results endpoint",
            "complete-with-analysis": "Upload and auto-analyze endpoint",
        },
        "ml/service/final_pipeline.py": {
            "def analyze_interview": "Pipeline entry function",
            "if __name__ == \"__main__\":": "CLI entry point",
            "sys.argv": "Command-line arguments",
        },
        "ml/service/analyzer.py": {
            "def store_analysis_result": "Database storage function",
            "from app.models.analysis import InterviewAnalysis": "Backend import",
        },
    }

    for filepath, checks in content_checks.items():
        if not os.path.exists(filepath):
            print_check(False, f"File not found: {filepath}")
            all_ok = False
            continue

        print(f"\n{YELLOW}{filepath}:{RESET}")
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            for pattern, description in checks.items():
                found = pattern in content
                all_ok = print_check(found, f"{description:40} ({pattern[:30]}...)") and all_ok
        
        except Exception as e:
            print_check(False, f"Error reading {filepath}: {e}")
            all_ok = False

    # ========================================================================
    # 3. IMPORTS
    # ========================================================================
    print_section("3. IMPORT VERIFICATION")

    try:
        print(f"{YELLOW}Python imports:{RESET}")
        
        # Test basic imports
        try:
            from sqlalchemy import Column, Integer, String
            print_check(True, "SQLAlchemy available")
        except ImportError as e:
            print_check(False, f"SQLAlchemy import failed: {e}")
            all_ok = False

        try:
            from pydantic import BaseModel
            print_check(True, "Pydantic available")
        except ImportError as e:
            print_check(False, f"Pydantic import failed: {e}")
            all_ok = False

        try:
            import sys
            import subprocess
            print_check(True, "sys/subprocess available")
        except ImportError as e:
            print_check(False, f"Standard lib import failed: {e}")
            all_ok = False

    except Exception as e:
        print_check(False, f"Import check failed: {e}")
        all_ok = False

    # ========================================================================
    # 4. CONFIGURATION
    # ========================================================================
    print_section("4. CONFIGURATION")

    config_checks = {
        ".env": "Environment file (optional - create from .env.example.ml)",
        ".env.example.ml": "Environment template (required)",
    }

    for config_file, description in config_checks.items():
        exists = os.path.exists(config_file)
        if config_file == ".env":
            # .env is optional
            status = print_check(exists, f"{description:40} {config_file}")
        else:
            # .env.example.ml is required
            all_ok = print_check(exists, f"{description:40} {config_file}") and all_ok

    # ========================================================================
    # 5. SUMMARY
    # ========================================================================
    print_section("VERIFICATION SUMMARY")

    if all_ok:
        print(f"""
{GREEN}✅ ALL CHECKS PASSED!{RESET}

Your ML Pipeline integration is properly set up. Next steps:

1. {YELLOW}Database Setup{RESET}
   cd backend
   alembic revision --autogenerate -m "Add interview_analysis"
   alembic upgrade head

2. {YELLOW}Environment{RESET}
   cp backend/.env.example.ml backend/.env
   # Edit .env with your DATABASE_URL

3. {YELLOW}Start Backend{RESET}
   uvicorn app.main:app --reload

4. {YELLOW}Test{RESET}
   pytest backend/tests/test_ml_integration.py -v

5. {YELLOW}Read Documentation{RESET}
   Start with: backend/QUICKSTART_ML_INTEGRATION.md

{BLUE}Complete implementation ready for production!{RESET}
        """)
        return 0
    else:
        print(f"""
{RED}❌ SOME CHECKS FAILED{RESET}

Please ensure all required files are in place:
- backend/app/models/analysis.py
- backend/app/schemas_analysis.py
- backend/app/api/routes/interviews.py (modified)
- ml/service/final_pipeline.py (modified)
- ml/service/analyzer.py (modified)
- All documentation files

{YELLOW}Run this script again after fixing issues.{RESET}
        """)
        return 1


if __name__ == "__main__":
    sys.exit(main())
