#!/usr/bin/env python3
"""
Verification script for auto-skip fixes.
Run from project root: python verify_fixes.py
"""

import os
import sys
import re

def check_file_content(filepath, pattern, description):
    """Check if a file contains expected pattern."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE):
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description}")
                return False
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return False
    except Exception as e:
        print(f"❌ Error checking {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("AUTO-SKIP FIXES VERIFICATION")
    print("=" * 60)
    
    all_pass = True
    
    # Check backend fixes
    print("\n[BACKEND FIXES]")
    
    interviews_py = "backend/app/api/routes/interviews.py"
    
    # Check submit_answer
    all_pass &= check_file_content(
        interviews_py,
        r'file_path = f"text-answer-\{interview_id\}-\{question_id\}',
        "submit_answer() has safe default file_path"
    )
    
    # Check candidate_answer
    all_pass &= check_file_content(
        interviews_py,
        r'@router\.post\(\'/candidate/interviews/\{interview_id\}/answer\'\).*file_path = f"text-answer',
        "candidate_answer() has safe default file_path"
    )
    
    # Check frontend fixes
    print("\n[FRONTEND FIXES]")
    
    runinterview_jsx = "frontend/src/pages/RunInterview.jsx"
    
    # Check VAD ranges
    all_pass &= check_file_content(
        runinterview_jsx,
        r'const SILENCE_MIN = -65;',
        "VAD has SILENCE_MIN constant"
    )
    
    all_pass &= check_file_content(
        runinterview_jsx,
        r'const SILENCE_MAX = -45;',
        "VAD has SILENCE_MAX constant"
    )
    
    all_pass &= check_file_content(
        runinterview_jsx,
        r'const isInSilenceRange = db >= SILENCE_MIN && db <= SILENCE_MAX;',
        "VAD uses stable silence range check"
    )
    
    all_pass &= check_file_content(
        runinterview_jsx,
        r'if \(silenceDuration >= SKIP_DELAY\)',
        "VAD has 5-second skip delay check"
    )
    
    # Check database model
    print("\n[DATABASE MODEL]")
    
    recording_py = "backend/app/models/recording.py"
    
    all_pass &= check_file_content(
        recording_py,
        r'file_path = Column\(String, nullable=True\)',
        "Recording.file_path is nullable"
    )
    
    # Check migration
    print("\n[DATABASE MIGRATION]")
    
    migration_file = "backend/migrations/versions/make_file_path_nullable.py"
    
    all_pass &= check_file_content(
        migration_file,
        r'def upgrade\(\):',
        "Migration file has upgrade() function"
    )
    
    all_pass &= check_file_content(
        migration_file,
        r'nullable=True',
        "Migration sets nullable=True"
    )
    
    # Summary
    print("\n" + "=" * 60)
    if all_pass:
        print("✅ ALL FIXES VERIFIED - Ready to deploy!")
        print("\nNext steps:")
        print("1. cd backend && alembic upgrade head")
        print("2. Restart backend server")
        print("3. Test manual skip and auto-skip")
    else:
        print("❌ SOME CHECKS FAILED - Review above")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
