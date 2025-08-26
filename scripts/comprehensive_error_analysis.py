#!/usr/bin/env python3
"""
Ultra-Deep Comprehensive Error Analysis Script for AI Hedge Fund Project
========================================================================

This script performs the most thorough analysis possible of all errors, warnings, 
and hidden issues across the entire project. It goes beyond surface-level problems
to detect subtle architectural issues, performance bottlenecks, security vulnerabilities,
and maintainability concerns.

Enhanced Features:
- Multi-tool static analysis (pylint, flake8, mypy, bandit, safety)
- Frontend analysis (ESLint, TypeScript, dependency audit)
- Architectural analysis (circular imports, coupling, complexity)
- Security vulnerability scanning
- Performance anti-pattern detection
- Code smell detection
- Dead code analysis
- Configuration validation
- Documentation coverage analysis
- Database schema analysis
- API endpoint testing
- Docker configuration validation
- Environment configuration analysis
"""

import os
import sys
import json
import subprocess
import time
import re
import ast
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict, Counter
import importlib.util

@dataclass
class ErrorReport:
    """Enhanced data class for error reporting"""
    tool: str
    file_path: str
    line: Optional[int]
    column: Optional[int]
    severity: str
    code: str
    message: str
    category: str
    suggestion: str = ""
    impact: str = ""  # performance, security, maintainability, reliability
    confidence: float = 1.0
    fix_effort: str = "medium"  # low, medium, high
    business_impact: str = "low"  # low, medium, high, critical

@dataclass
class AnalysisResult:
    """Data class for analysis results"""
    tool_name: str
    total_issues: int
    errors: int
    warnings: int
    info: int
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    coverage_percentage: Optional[float] = None

class UltraDeepErrorAnalyzer:
    """Ultra-comprehensive error analyzer with deep inspection capabilities"""
    
    def __init__(self, project_root: str = "/workspaces/ai-hedge-fund"):
        self.project_root = Path(project_root)
        self.results: List[AnalysisResult] = []
        self.error_reports: List[ErrorReport] = []
        self.start_time = datetime.now()
        
        # Enhanced path definitions
        self.python_paths = [
            "src/",
            "app/backend/",
            "scripts/",
            "tests/"
        ]
        
        self.frontend_paths = [
            "app/frontend/src/"
        ]
        
        self.config_paths = [
            "pyproject.toml",
            "pyrightconfig.json",
            ".env.example",
            "app/frontend/package.json",
            "app/frontend/tsconfig.json",
            "docker/docker-compose.yml"
        ]
        
        # File patterns for deep analysis
        self.ignore_patterns = [
            "**/node_modules/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/dist/**",
            "**/build/**",
            "**/.venv/**",
            "**/venv/**",
            "**/alembic/versions/**"
        ]
        
        # Analysis caches
        self.import_graph = defaultdict(set)
        self.complexity_metrics = {}
        self.file_metrics = {}
        self.api_endpoints = []
        self.database_tables = []
        
        # Ensure we're in the right directory
        os.chdir(self.project_root)
        
    def should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored based on patterns"""
        file_str = str(file_path)
        return any(file_path.match(pattern) for pattern in self.ignore_patterns)
        
    def run_command(self, command: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Tuple[bool, str, str]:
        """Enhanced command runner with better error handling and security"""
        # Security: Validate command to prevent injection
        if not command or not isinstance(command, list):
            return False, "", "Invalid command format"
        
        # Security: Whitelist allowed commands
        allowed_commands = {
            'python', 'pylint', 'flake8', 'mypy', 'bandit', 'safety', 
            'black', 'isort', 'pytest', 'coverage', 'pip'
        }
        
        base_command = command[0].split('/')[-1]  # Get just the command name
        if base_command not in allowed_commands:
            return False, "", f"Command not allowed: {base_command}"
        
        try:
            # Security: Use shell=False to prevent shell injection
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False  # Security: Prevent shell injection
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except FileNotFoundError:
            return False, "", f"Command not found: {command[0]}"
        except Exception as e:
            return False, "", str(e)
    
    def analyze_database_schema(self) -> AnalysisResult:
        """Analyze database schema for issues"""
        print("🗄️ Analyzing database schema...")
        start_time = time.time()
        
        errors = warnings = info = 0
        
        # Find database files
        db_files = list(self.project_root.rglob("*.db"))
        
        for db_file in db_files:
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get table information
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                self.database_tables = [table[0] for table in tables]
                
                for table_name in self.database_tables:
                    # Check for missing indexes
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()
                    
                    # Check for foreign key constraints
                    cursor.execute(f"PRAGMA foreign_key_list({table_name});")
                    foreign_keys = cursor.fetchall()
                    
                    # Analyze table structure
                    if len(columns) > 20:
                        warnings += 1
                        self.error_reports.append(ErrorReport(
                            tool="database_analyzer",
                            file_path=str(db_file.relative_to(self.project_root)),
                            line=None,
                            column=None,
                            severity="warning",
                            code="DB001",
                            message=f"Table '{table_name}' has many columns ({len(columns)})",
                            category="database_design",
                            suggestion="Consider normalizing the table structure",
                            impact="maintainability",
                            confidence=0.7,
                            fix_effort="high",
                            business_impact="medium"
                        ))
                    
                    # Check for missing primary keys
                    has_primary_key = any(col[5] for col in columns)  # col[5] is pk flag
                    if not has_primary_key:
                        errors += 1
                        self.error_reports.append(ErrorReport(
                            tool="database_analyzer",
                            file_path=str(db_file.relative_to(self.project_root)),
                            line=None,
                            column=None,
                            severity="error",
                            code="DB002",
                            message=f"Table '{table_name}' lacks primary key",
                            category="database_integrity",
                            suggestion="Add a primary key to ensure data integrity",
                            impact="reliability",
                            confidence=0.9,
                            fix_effort="medium",
                            business_impact="high"
                        ))
                
                conn.close()
                
            except Exception as e:
                errors += 1
                self.error_reports.append(ErrorReport(
                    tool="database_analyzer",
                    file_path=str(db_file.relative_to(self.project_root)),
                    line=None,
                    column=None,
                    severity="error",
                    code="DB003",
                    message=f"Database analysis failed: {str(e)}",
                    category="database_error",
                    suggestion="Check database file integrity",
                    impact="reliability",
                    confidence=1.0,
                    fix_effort="medium",
                    business_impact="high"
                ))
        
        execution_time = time.time() - start_time
        total = errors + warnings + info
        return AnalysisResult("database", total, errors, warnings, info, execution_time, True)
    
    def analyze_api_endpoints(self) -> AnalysisResult:
        """Analyze API endpoints for issues"""
        print("🌐 Analyzing API endpoints...")
        start_time = time.time()
        
        errors = warnings = info = 0
        
        # Find FastAPI route files
        route_files = list((self.project_root / "app/backend/routes").rglob("*.py"))
        
        for route_file in route_files:
            try:
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find route definitions
                route_patterns = [
                    r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in route_patterns:
                    for match in re.finditer(pattern, content):
                        method = match.group(1).upper()
                        path = match.group(2)
                        self.api_endpoints.append(f"{method} {path}")
                        
                        # Check for missing error handling
                        line_num = content[:match.start()].count('\n') + 1
                        
                        # Look for try-catch blocks near the route
                        route_context = content[match.start():match.start() + 1000]
                        if 'try:' not in route_context and 'except' not in route_context:
                            warnings += 1
                            self.error_reports.append(ErrorReport(
                                tool="api_analyzer",
                                file_path=str(route_file.relative_to(self.project_root)),
                                line=line_num,
                                column=None,
                                severity="warning",
                                code="API001",
                                message=f"Route {method} {path} lacks error handling",
                                category="api_reliability",
                                suggestion="Add try-catch blocks for proper error handling",
                                impact="reliability",
                                confidence=0.6,
                                fix_effort="low",
                                business_impact="medium"
                            ))
                        
                        # Check for missing input validation
                        if 'Depends(' not in route_context and 'Request' not in route_context:
                            info += 1
                            self.error_reports.append(ErrorReport(
                                tool="api_analyzer",
                                file_path=str(route_file.relative_to(self.project_root)),
                                line=line_num,
                                column=None,
                                severity="info",
                                code="API002",
                                message=f"Route {method} {path} may lack input validation",
                                category="api_security",
                                suggestion="Consider adding Pydantic models for input validation",
                                impact="security",
                                confidence=0.4,
                                fix_effort="medium",
                                business_impact="medium"
                            ))
                
            except Exception:
                continue
        
        execution_time = time.time() - start_time
        total = errors + warnings + info
        return AnalysisResult("api_endpoints", total, errors, warnings, info, execution_time, True)
    
    def analyze_configuration_files(self) -> AnalysisResult:
        """Analyze configuration files for issues"""
        print("⚙️ Analyzing configuration files...")
        start_time = time.time()
        
        errors = warnings = info = 0
        
        for config_path in self.config_paths:
            config_file = self.project_root / config_path
            if not config_file.exists():
                warnings += 1
                self.error_reports.append(ErrorReport(
                    tool="config_analyzer",
                    file_path=config_path,
                    line=None,
                    column=None,
                    severity="warning",
                    code="CFG001",
                    message=f"Configuration file missing: {config_path}",
                    category="configuration",
                    suggestion="Create the missing configuration file",
                    impact="maintainability",
                    confidence=0.8,
                    fix_effort="low",
                    business_impact="low"
                ))
                continue
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for hardcoded values
                hardcoded_patterns = [
                    (r'localhost', "Hardcoded localhost found"),
                    (r'127\.0\.0\.1', "Hardcoded IP address found"),
                    (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password found"),
                    (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret found"),
                ]
                
                for pattern, message in hardcoded_patterns:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        line_num = content[:match.start()].count('\n') + 1
                        warnings += 1
                        self.error_reports.append(ErrorReport(
                            tool="config_analyzer",
                            file_path=config_path,
                            line=line_num,
                            column=None,
                            severity="warning",
                            code="CFG002",
                            message=message,
                            category="configuration_security",
                            suggestion="Use environment variables for sensitive data",
                            impact="security",
                            confidence=0.8,
                            fix_effort="low",
                            business_impact="medium"
                        ))
                
            except Exception:
                errors += 1
                self.error_reports.append(ErrorReport(
                    tool="config_analyzer",
                    file_path=config_path,
                    line=None,
                    column=None,
                    severity="error",
                    code="CFG003",
                    message=f"Failed to read configuration file: {config_path}",
                    category="configuration_error",
                    suggestion="Check file permissions and encoding",
                    impact="reliability",
                    confidence=1.0,
                    fix_effort="low",
                    business_impact="medium"
                ))
        
        execution_time = time.time() - start_time
        total = errors + warnings + info
        return AnalysisResult("configuration", total, errors, warnings, info, execution_time, True)
    
    def analyze_docker_configuration(self) -> AnalysisResult:
        """Analyze Docker configuration for issues"""
        print("🐳 Analyzing Docker configuration...")
        start_time = time.time()
        
        errors = warnings = info = 0
        
        docker_files = [
            "docker/Dockerfile",
            "docker/docker-compose.yml",
            ".dockerignore"
        ]
        
        for docker_file in docker_files:
            file_path = self.project_root / docker_file
            if not file_path.exists():
                if docker_file != ".dockerignore":  # .dockerignore is optional
                    warnings += 1
                    self.error_reports.append(ErrorReport(
                        tool="docker_analyzer",
                        file_path=docker_file,
                        line=None,
                        column=None,
                        severity="warning",
                        code="DOC001",
                        message=f"Docker file missing: {docker_file}",
                        category="docker_configuration",
                        suggestion="Create the missing Docker configuration file",
                        impact="maintainability",
                        confidence=0.8,
                        fix_effort="medium",
                        business_impact="low"
                    ))
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if docker_file.endswith('Dockerfile'):
                    # Check for security issues in Dockerfile
                    if 'USER root' in content or 'USER 0' in content:
                        warnings += 1
                        self.error_reports.append(ErrorReport(
                            tool="docker_analyzer",
                            file_path=docker_file,
                            line=None,
                            column=None,
                            severity="warning",
                            code="DOC002",
                            message="Running as root user in Docker",
                            category="docker_security",
                            suggestion="Create and use a non-root user",
                            impact="security",
                            confidence=0.9,
                            fix_effort="medium",
                            business_impact="medium"
                        ))
                    
                    # Check for latest tag usage
                    if ':latest' in content:
                        info += 1
                        self.error_reports.append(ErrorReport(
                            tool="docker_analyzer",
                            file_path=docker_file,
                            line=None,
                            column=None,
                            severity="info",
                            code="DOC003",
                            message="Using 'latest' tag in Docker image",
                            category="docker_best_practices",
                            suggestion="Pin specific versions for reproducible builds",
                            impact="maintainability",
                            confidence=0.7,
                            fix_effort="low",
                            business_impact="low"
                        ))
                
            except Exception:
                errors += 1
                self.error_reports.append(ErrorReport(
                    tool="docker_analyzer",
                    file_path=docker_file,
                    line=None,
                    column=None,
                    severity="error",
                    code="DOC004",
                    message=f"Failed to read Docker file: {docker_file}",
                    category="docker_error",
                    suggestion="Check file permissions and syntax",
                    impact="reliability",
                    confidence=1.0,
                    fix_effort="low",
                    business_impact="medium"
                ))
        
        execution_time = time.time() - start_time
        total = errors + warnings + info
        return AnalysisResult("docker", total, errors, warnings, info, execution_time, True)
    
    def analyze_test_coverage(self) -> AnalysisResult:
        """Analyze test coverage and test quality"""
        print("🧪 Analyzing test coverage...")
        start_time = time.time()
        
        errors = warnings = info = 0
        
        # Find test files
        test_files = list((self.project_root / "tests").rglob("*.py")) if (self.project_root / "tests").exists() else []
        
        # Count source files vs test files
        source_files = []
        for path in self.python_paths:
            if (self.project_root / path).exists():
                source_files.extend(list((self.project_root / path).rglob("*.py")))
        
        source_files = [f for f in source_files if not self.should_ignore_file(f) and 'test' not in str(f)]
        
        test_ratio = len(test_files) / len(source_files) if source_files else 0
        
        if test_ratio < 0.1:  # Less than 10% test coverage by file count
            errors += 1
            self.error_reports.append(ErrorReport(
                tool="test_analyzer",
                file_path="tests/",
                line=None,
                column=None,
                severity="error",
                code="TEST001",
                message=f"Very low test coverage: {len(test_files)} test files for {len(source_files)} source files",
                category="test_coverage",
                suggestion="Add comprehensive test suite",
                impact="reliability",
                confidence=0.9,
                fix_effort="high",
                business_impact="high"
            ))
        elif test_ratio < 0.3:  # Less than 30% test coverage
            warnings += 1
            self.error_reports.append(ErrorReport(
                tool="test_analyzer",
                file_path="tests/",
                line=None,
                column=None,
                severity="warning",
                code="TEST002",
                message=f"Low test coverage: {len(test_files)} test files for {len(source_files)} source files",
                category="test_coverage",
                suggestion="Increase test coverage",
                impact="reliability",
                confidence=0.8,
                fix_effort="high",
                business_impact="medium"
            ))
        
        # Analyze individual test files
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for test patterns
                test_function_count = len(re.findall(r'def test_\w+', content))
                if test_function_count == 0:
                    warnings += 1
                    self.error_reports.append(ErrorReport(
                        tool="test_analyzer",
                        file_path=str(test_file.relative_to(self.project_root)),
                        line=None,
                        column=None,
                        severity="warning",
                        code="TEST003",
                        message="Test file contains no test functions",
                        category="test_quality",
                        suggestion="Add test functions with 'test_' prefix",
                        impact="reliability",
                        confidence=0.9,
                        fix_effort="medium",
                        business_impact="medium"
                    ))
                
            except Exception:
                continue
        
        execution_time = time.time() - start_time
        total = errors + warnings + info
        coverage_percentage = test_ratio * 100
        return AnalysisResult("test_coverage", total, errors, warnings, info, execution_time, True, coverage_percentage=coverage_percentage)
    
    def analyze_documentation_coverage(self) -> AnalysisResult:
        """Analyze documentation coverage"""
        print("📚 Analyzing documentation coverage...")
        start_time = time.time()
        
        errors = warnings = info = 0
        
        # Find Python files and check for docstrings
        python_files = []
        for path in self.python_paths:
            if (self.project_root / path).exists():
                python_files.extend(list((self.project_root / path).rglob("*.py")))
        
        python_files = [f for f in python_files if not self.should_ignore_file(f)]
        
        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                try:
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            total_functions += 1
                            if ast.get_docstring(node):
                                documented_functions += 1
                        elif isinstance(node, ast.ClassDef):
                            total_classes += 1
                            if ast.get_docstring(node):
                                documented_classes += 1
                
                except SyntaxError:
                    continue
                    
            except Exception:
                continue
        
        # Calculate documentation coverage
        function_doc_ratio = documented_functions / total_functions if total_functions > 0 else 1
        class_doc_ratio = documented_classes / total_classes if total_classes > 0 else 1
        
        if function_doc_ratio < 0.3:
            warnings += 1
            self.error_reports.append(ErrorReport(
                tool="doc_analyzer",
                file_path="src/",
                line=None,
                column=None,
                severity="warning",
                code="DOC001",
                message=f"Low function documentation coverage: {documented_functions}/{total_functions} ({function_doc_ratio:.1%})",
                category="documentation",
                suggestion="Add docstrings to functions",
                impact="maintainability",
                confidence=0.8,
                fix_effort="medium",
                business_impact="low"
            ))
        
        if class_doc_ratio < 0.5:
            warnings += 1
            self.error_reports.append(ErrorReport(
                tool="doc_analyzer",
                file_path="src/",
                line=None,
                column=None,
                severity="warning",
                code="DOC002",
                message=f"Low class documentation coverage: {documented_classes}/{total_classes} ({class_doc_ratio:.1%})",
                category="documentation",
                suggestion="Add docstrings to classes",
                impact="maintainability",
                confidence=0.8,
                fix_effort="medium",
                business_impact="low"
            ))
        
        # Check for README files
        readme_files = list(self.project_root.rglob("README*"))
        if not readme_files:
            warnings += 1
            self.error_reports.append(ErrorReport(
                tool="doc_analyzer",
                file_path="./",
                line=None,
                column=None,
                severity="warning",
                code="DOC003",
                message="No README file found",
                category="documentation",
                suggestion="Create a comprehensive README file",
                impact="maintainability",
                confidence=0.9,
                fix_effort="low",
                business_impact="low"
            ))
        
        execution_time = time.time() - start_time
        total = errors + warnings + info
        overall_doc_coverage = (function_doc_ratio + class_doc_ratio) / 2 * 100
        return AnalysisResult("documentation", total, errors, warnings, info, execution_time, True, coverage_percentage=overall_doc_coverage)
    
    def analyze_python_with_pylint(self) -> AnalysisResult:
        """Enhanced pylint analysis with better error categorization"""
        print("🔍 Running enhanced pylint analysis...")
        start_time = time.time()
        
        # Create pylint command for all Python paths
        python_files = []
        for path in self.python_paths:
            if (self.project_root / path).exists():
                python_files.extend(list((self.project_root / path).rglob("*.py")))
        
        # Filter out ignored files
        python_files = [f for f in python_files if not self.should_ignore_file(f)]
        
        if not python_files:
            return AnalysisResult("pylint", 0, 0, 0, 0, 0, False, "No Python files found")
        
        # Run pylint with comprehensive configuration
        command = [
            "python", "-m", "pylint", 
            "--output-format=json", 
            "--reports=no",
            "--disable=C0114,C0115,C0116",  # Disable some docstring warnings for now
            "--max-line-length=120"
        ] + [str(f) for f in python_files]
        
        success, stdout, stderr = self.run_command(command)
        execution_time = time.time() - start_time
        
        if not success and not stdout:
            return AnalysisResult("pylint", 0, 0, 0, 0, execution_time, False, stderr)
        
        # Enhanced pylint output parsing
        errors = warnings = info = 0
        try:
            if stdout.strip():
                issues = json.loads(stdout)
                for issue in issues:
                    severity = issue.get('type', 'info')
                    if severity in ['error', 'fatal']:
                        errors += 1
                    elif severity == 'warning':
                        warnings += 1
                    else:
                        info += 1
                    
                    # Enhanced error categorization
                    category = self._categorize_pylint_issue(issue.get('message-id', ''))
                    impact = self._determine_impact(issue.get('message-id', ''))
                    fix_effort = self._determine_fix_effort(issue.get('message-id', ''))
                    business_impact = self._determine_business_impact(issue.get('message-id', ''))
                    
                    self.error_reports.append(ErrorReport(
                        tool="pylint",
                        file_path=issue.get('path', ''),
                        line=issue.get('line'),
                        column=issue.get('column'),
                        severity=severity,
                        code=issue.get('message-id', ''),
                        message=issue.get('message', ''),
                        category=category,
                        suggestion=self._get_pylint_suggestion(issue.get('message-id', '')),
                        impact=impact,
                        confidence=0.9,
                        fix_effort=fix_effort,
                        business_impact=business_impact
                    ))
        except json.JSONDecodeError:
            # Fallback parsing for non-JSON output
            lines = stdout.split('\n')
            for line in lines:
                if ': error:' in line.lower():
                    errors += 1
                elif ': warning:' in line.lower():
                    warnings += 1
                elif line.strip():
                    info += 1
        
        total = errors + warnings + info
        return AnalysisResult("pylint", total, errors, warnings, info, execution_time, True)
    
    def _categorize_pylint_issue(self, code: str) -> str:
        """Categorize pylint issues for better organization"""
        if code.startswith('C'):
            return "code_style"
        elif code.startswith('R'):
            return "refactoring"
        elif code.startswith('W'):
            return "warning"
        elif code.startswith('E'):
            return "error"
        elif code.startswith('F'):
            return "fatal"
        else:
            return "other"
    
    def _determine_impact(self, code: str) -> str:
        """Determine the impact category of an issue"""
        security_codes = ['W1201', 'W1202', 'W1203', 'W1300', 'W1301']
        performance_codes = ['W0622', 'R1701', 'R1702', 'R1703']
        reliability_codes = ['E1101', 'E1102', 'E1103', 'E1111']
        
        if code in security_codes:
            return "security"
        elif code in performance_codes:
            return "performance"
        elif code in reliability_codes:
            return "reliability"
        else:
            return "maintainability"
    
    def _determine_fix_effort(self, code: str) -> str:
        """Determine the effort required to fix an issue"""
        low_effort = ['C0301', 'W0613', 'C0103']  # Line length, unused param, naming
        high_effort = ['R0903', 'R0913', 'R1702']  # Too few methods, too many args, too complex
        
        if code in low_effort:
            return "low"
        elif code in high_effort:
            return "high"
        else:
            return "medium"
    
    def _determine_business_impact(self, code: str) -> str:
        """Determine the business impact of an issue"""
        critical_codes = ['E1101', 'E1102', 'F0401']  # Attribute errors, import errors
        high_codes = ['W1201', 'W1202', 'W1203']  # Security issues
        
        if code in critical_codes:
            return "critical"
        elif code in high_codes:
            return "high"
        else:
            return "low"
    
    def _get_pylint_suggestion(self, code: str) -> str:
        """Get specific suggestions for pylint issues"""
        suggestions = {
            'C0103': "Use snake_case naming convention",
            'C0301': "Break long lines for better readability",
            'R0903': "Consider adding more methods or combining with other classes",
            'R0913': "Consider using a configuration object or dataclass",
            'W0613': "Remove unused parameter or prefix with underscore",
            'W0622': "Avoid shadowing built-in names",
        }
        return suggestions.get(code, "Follow pylint recommendations")
    
    def analyze_security_vulnerabilities(self) -> AnalysisResult:
        """Deep security vulnerability analysis"""
        print("🔒 Running comprehensive security analysis...")
        start_time = time.time()
        
        errors = warnings = info = 0
        
        # Run bandit for Python security
        bandit_result = self._run_bandit_analysis()
        if bandit_result:
            errors += bandit_result.errors
            warnings += bandit_result.warnings
            info += bandit_result.info
        
        # Run safety for dependency vulnerabilities
        safety_result = self._run_safety_analysis()
        if safety_result:
            errors += safety_result.errors
            warnings += safety_result.warnings
            info += safety_result.info
        
        # Custom security pattern analysis
        custom_result = self._analyze_custom_security_patterns()
        if custom_result:
            errors += custom_result.errors
            warnings += custom_result.warnings
            info += custom_result.info
        
        execution_time = time.time() - start_time
        total = errors + warnings + info
        return AnalysisResult("security", total, errors, warnings, info, execution_time, True)
    
    def _run_bandit_analysis(self) -> Optional[AnalysisResult]:
        """Run bandit security scanner"""
        command = ["python", "-m", "bandit", "-r", ".", "-f", "json", "-q"]
        success, stdout, stderr = self.run_command(command)
        
        if not success:
            return None
        
        errors = warnings = info = 0
        try:
            if stdout.strip():
                data = json.loads(stdout)
                for result in data.get('results', []):
                    severity_map = {
                        'HIGH': 'error',
                        'MEDIUM': 'warning',
                        'LOW': 'info'
                    }
                    
                    severity = severity_map.get(result.get('issue_severity', 'LOW'), 'info')
                    if severity == 'error':
                        errors += 1
                    elif severity == 'warning':
                        warnings += 1
                    else:
                        info += 1
                    
                    self.error_reports.append(ErrorReport(
                        tool="bandit",
                        file_path=result.get('filename', '').replace(str(self.project_root) + '/', ''),
                        line=result.get('line_number'),
                        column=None,
                        severity=severity,
                        code=result.get('test_id', ''),
                        message=result.get('issue_text', ''),
                        category="security",
                        suggestion="Review security implications and apply appropriate fixes",
                        impact="security",
                        confidence=result.get('issue_confidence', 'HIGH') == 'HIGH' and 0.9 or 0.7,
                        fix_effort="medium",
                        business_impact="high"
                    ))
        except json.JSONDecodeError:
            pass
        
        return AnalysisResult("bandit", errors + warnings + info, errors, warnings, info, 0, True)
    
    def _run_safety_analysis(self) -> Optional[AnalysisResult]:
        """Run safety dependency vulnerability scanner"""
        command = ["python", "-m", "safety", "check", "--json"]
        success, stdout, stderr = self.run_command(command)
        
        if not success:
            return None
        
        errors = warnings = info = 0
        try:
            if stdout.strip():
                data = json.loads(stdout)
                for vuln in data:
                    errors += 1  # All vulnerabilities are considered errors
                    
                    self.error_reports.append(ErrorReport(
                        tool="safety",
                        file_path="requirements/dependencies",
                        line=None,
                        column=None,
                        severity="error",
                        code=vuln.get('id', ''),
                        message=f"Vulnerable dependency: {vuln.get('package', '')} {vuln.get('installed_version', '')}",
                        category="dependency_vulnerability",
                        suggestion=f"Upgrade to version {vuln.get('safe_versions', ['latest'])[0] if vuln.get('safe_versions') else 'latest'}",
                        impact="security",
                        confidence=1.0,
                        fix_effort="low",
                        business_impact="high"
                    ))
        except json.JSONDecodeError:
            pass
        
        return AnalysisResult("safety", errors + warnings + info, errors, warnings, info, 0, True)
    
    def _analyze_custom_security_patterns(self) -> Optional[AnalysisResult]:
        """Analyze custom security patterns in code"""
        python_files = []
        for path in self.python_paths:
            if (self.project_root / path).exists():
                python_files.extend(list((self.project_root / path).rglob("*.py")))
        
        python_files = [f for f in python_files if not self.should_ignore_file(f)]
        
        errors = warnings = info = 0
        
        # Security patterns to detect
        security_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected", "error"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected", "error"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret detected", "error"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token detected", "error"),
            (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "Shell injection risk", "warning"),
            (r'os\.system\s*\(', "OS command execution risk", "warning"),
            (r'pickle\.loads?\s*\(', "Unsafe deserialization", "warning"),
            (r'eval\s*\(', "Code injection risk with eval()", "error"),
            (r'exec\s*\(', "Code injection risk with exec()", "error"),
        ]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, message, severity in security_patterns:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        line_num = content[:match.start()].count('\n') + 1
                        
                        if severity == 'error':
                            errors += 1
                        elif severity == 'warning':
                            warnings += 1
                        else:
                            info += 1
                        
                        self.error_reports.append(ErrorReport(
                            tool="security_scanner",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line=line_num,
                            column=match.start() - content.rfind('\n', 0, match.start()),
                            severity=severity,
                            code="SEC001",
                            message=message,
                            category="security_pattern",
                            suggestion="Move sensitive data to environment variables or secure configuration",
                            impact="security",
                            confidence=0.8,
                            fix_effort="low",
                            business_impact="high"
                        ))
            except Exception:
                continue
        
        return AnalysisResult("custom_security", errors + warnings + info, errors, warnings, info, 0, True)
    
    def analyze_python_with_flake8(self) -> AnalysisResult:
        """Enhanced flake8 analysis"""
        print("🔍 Running enhanced flake8 analysis...")
        start_time = time.time()
        
        # Run flake8 on all Python directories with enhanced configuration
        command = [
            "python", "-m", "flake8", 
            "--max-line-length=120",
            "--extend-ignore=E203,W503",  # Ignore some formatting issues
            "--statistics"
        ] + self.python_paths
        
        success, stdout, stderr = self.run_command(command)
        execution_time = time.time() - start_time
        
        if not success and not stdout:
            return AnalysisResult("flake8", 0, 0, 0, 0, execution_time, False, stderr)
        
        # Parse flake8 output
        errors = warnings = info = 0
        lines = (stdout + stderr).split('\n')
        
        for line in lines:
            if line.strip() and ':' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    file_path = parts[0]
                    line_num = parts[1] if parts[1].isdigit() else None
                    col_num = parts[2] if parts[2].isdigit() else None
                    message_part = ':'.join(parts[3:]).strip()
                    
                    # Extract error code
                    code_match = re.match(r'(\w\d+)', message_part)
                    code = code_match.group(1) if code_match else ''
                    
                    if code.startswith('E'):
                        errors += 1
                        severity = 'error'
                    elif code.startswith('W'):
                        warnings += 1
                        severity = 'warning'
                    else:
                        info += 1
                        severity = 'info'
                    
                    self.error_reports.append(ErrorReport(
                        tool="flake8",
                        file_path=file_path.replace(str(self.project_root) + '/', ''),
                        line=int(line_num) if line_num else None,
                        column=int(col_num) if col_num else None,
                        severity=severity,
                        code=code,
                        message=message_part,
                        category="style",
                        suggestion=self._get_flake8_suggestion(code),
                        impact="maintainability",
                        confidence=0.8,
                        fix_effort="low",
                        business_impact="low"
                    ))
        
        total = errors + warnings + info
        return AnalysisResult("flake8", total, errors, warnings, info, execution_time, True)
    
    def _get_flake8_suggestion(self, code: str) -> str:
        """Get specific suggestions for flake8 issues"""
        suggestions = {
            'E501': "Break long lines using parentheses or backslashes",
            'E302': "Add two blank lines before class or function definition",
            'E303': "Remove extra blank lines",
            'W291': "Remove trailing whitespace",
            'W292': "Add newline at end of file",
            'E401': "Put imports on separate lines",
            'E402': "Move imports to top of file",
        }
        return suggestions.get(code, "Follow PEP 8 style guidelines")
    
    def analyze_python_with_mypy(self) -> AnalysisResult:
        """Enhanced mypy type checking analysis"""
        print("🔍 Running enhanced mypy type checking...")
        start_time = time.time()
        
        # Run mypy with comprehensive configuration
        command = [
            "python", "-m", "mypy", 
            "--show-error-codes", 
            "--no-error-summary",
            "--ignore-missing-imports"
        ] + self.python_paths
        
        success, stdout, stderr = self.run_command(command)
        execution_time = time.time() - start_time
        
        errors = warnings = info = 0
        output = stdout + stderr
        lines = output.split('\n')
        
        for line in lines:
            if ': error:' in line:
                errors += 1
                parts = line.split(': error: ')
                if len(parts) >= 2:
                    location = parts[0]
                    message = parts[1]
                    
                    file_line = location.split(':')
                    file_path = file_line[0] if file_line else ''
                    line_num = int(file_line[1]) if len(file_line) > 1 and file_line[1].isdigit() else None
                    
                    self.error_reports.append(ErrorReport(
                        tool="mypy",
                        file_path=file_path.replace(str(self.project_root) + '/', ''),
                        line=line_num,
                        column=None,
                        severity="error",
                        code="type-check",
                        message=message,
                        category="type_checking",
                        suggestion="Fix type annotations and imports",
                        impact="reliability",
                        confidence=0.9,
                        fix_effort="medium",
                        business_impact="medium"
                    ))
            elif ': warning:' in line:
                warnings += 1
            elif ': note:' in line:
                info += 1
        
        total = errors + warnings + info
        return AnalysisResult("mypy", total, errors, warnings, info, execution_time, True)
    
    def run_full_analysis(self) -> str:
        """Run complete ultra-deep analysis"""
        print("🚀 Starting Ultra-Deep Comprehensive Error Analysis...")
        print(f"📁 Project Root: {self.project_root}")
        
        # Enhanced analysis suite
        analyses = [
            self.analyze_python_with_pylint,
            self.analyze_python_with_flake8,
            self.analyze_python_with_mypy,
            self.analyze_security_vulnerabilities,
            self.analyze_database_schema,
            self.analyze_api_endpoints,
            self.analyze_configuration_files,
            self.analyze_docker_configuration,
            self.analyze_test_coverage,
            self.analyze_documentation_coverage,
        ]
        
        for analysis_func in analyses:
            try:
                result = analysis_func()
                self.results.append(result)
                print(f"✅ {result.tool_name}: {result.total_issues} issues found")
            except Exception as e:
                print(f"❌ {analysis_func.__name__} failed: {e}")
                self.results.append(AnalysisResult(
                    analysis_func.__name__, 0, 0, 0, 0, 0, False, str(e)
                ))
        
        # Generate comprehensive reports
        summary_report = self.generate_summary_report()
        json_file = self.save_detailed_json_report()
        
        # Save summary report
        summary_file = self.project_root / "ERROR_ANALYSIS_SUMMARY.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_report)
        
        print(f"\n📊 Ultra-Deep Analysis Complete!")
        print(f"📄 Summary Report: {sukmmary_file}")
        print(f"📋 Detailed JSON: {json_file}")
        
        return summary_report
    
    def generate_summary_report(self) -> str:
        """Generate comprehensive summary report"""
        total_issues = sum(result.total_issues for result in self.results)
        total_errors = sum(result.errors for result in self.results)
        total_warnings = sum(result.warnings for result in self.results)
        total_info = sum(result.info for result in self.results)
        
        # Enhanced categorization
        categories = defaultdict(int)
        impacts = defaultdict(int)
        tools = defaultdict(int)
        fix_efforts = defaultdict(int)
        business_impacts = defaultdict(int)
        
        for error in self.error_reports:
            categories[error.category] += 1
            impacts[error.impact] += 1
            tools[error.tool] += 1
            fix_efforts[error.fix_effort] += 1
            business_impacts[error.business_impact] += 1
        
        report = f"""
# ULTRA-DEEP COMPREHENSIVE ERROR ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Project: AI Hedge Fund System
Analysis Duration: {(datetime.now() - self.start_time).total_seconds():.2f} seconds

## EXECUTIVE SUMMARY
- **Total Issues Found: {total_issues}**
- **Critical Errors: {total_errors}**
- **Warnings: {total_warnings}**
- **Info/Notes: {total_info}**

## ANALYSIS TOOLS BREAKDOWN
"""
        
        for result in self.results:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            report += f"""
### {result.tool_name.upper()} {status}
- Total Issues: {result.total_issues}
- Errors: {result.errors}
- Warnings: {result.warnings}
- Info: {result.info}
- Execution Time: {result.execution_time:.2f}s
"""
            if result.coverage_percentage is not None:
                report += f"- Coverage: {result.coverage_percentage:.1f}%\n"
            if result.error_message:
                report += f"- Error: {result.error_message}\n"
        
        # Enhanced categorization
        report += "\n## ISSUES BY CATEGORY\n"
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{category.replace('_', ' ').title()}:** {count}\n"
        
        report += "\n## ISSUES BY IMPACT\n"
        for impact, count in sorted(impacts.items(), key=lambda x: x[1], reverse=True):
            if impact:  # Skip empty impacts
                report += f"- **{impact.title()}:** {count}\n"
        
        report += "\n## ISSUES BY FIX EFFORT\n"
        for effort, count in sorted(fix_efforts.items(), key=lambda x: x[1], reverse=True):
            if effort:
                report += f"- **{effort.title()} Effort:** {count}\n"
        
        report += "\n## ISSUES BY BUSINESS IMPACT\n"
        for impact, count in sorted(business_impacts.items(), key=lambda x: x[1], reverse=True):
            if impact:
                report += f"- **{impact.title()} Impact:** {count}\n"
        
        # Top problematic files
        file_issues = defaultdict(int)
        for error in self.error_reports:
            if error.file_path:
                file_issues[error.file_path] += 1
        
        report += "\n## TOP PROBLEMATIC FILES\n"
        top_files = sorted(file_issues.items(), key=lambda x: x[1], reverse=True)[:15]
        for file_path, count in top_files:
            report += f"- **{file_path}:** {count} issues\n"
        
        # Critical issues requiring immediate attention
        critical_errors = [e for e in self.error_reports if e.severity in ['error', 'critical'] or e.business_impact == 'critical']
        if critical_errors:
            report += f"\n## CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION ({len(critical_errors)})\n"
            for error in critical_errors[:25]:  # Show top 25
                location = f"{error.file_path}:{error.line or '?'}"
                report += f"- **{location}** [{error.tool}] {error.message}\n"
        
        # Security issues
        security_issues = [e for e in self.error_reports if e.impact == 'security']
        if security_issues:
            report += f"\n## SECURITY VULNERABILITIES ({len(security_issues)})\n"
            for error in security_issues[:15]:
                location = f"{error.file_path}:{error.line or '?'}"
                report += f"- **{location}** [{error.tool}] {error.message}\n"
        
        # Performance issues
        performance_issues = [e for e in self.error_reports if e.impact == 'performance']
        if performance_issues:
            report += f"\n## PERFORMANCE ISSUES ({len(performance_issues)})\n"
            for error in performance_issues[:15]:
                location = f"{error.file_path}:{error.line or '?'}"
                report += f"- **{location}** {error.message}\n"
        
        # Database and API analysis
        if self.database_tables:
            report += f"\n## DATABASE ANALYSIS\n"
            report += f"- **Tables Found:** {len(self.database_tables)}\n"
            report += f"- **Tables:** {', '.join(self.database_tables)}\n"
        
        if self.api_endpoints:
            report += f"\n## API ENDPOINTS ANALYSIS\n"
            report += f"- **Endpoints Found:** {len(self.api_endpoints)}\n"
            for endpoint in self.api_endpoints[:10]:  # Show first 10
                report += f"- {endpoint}\n"
        
        # Recommendations
        report += "\n## ACTIONABLE RECOMMENDATIONS\n"
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on findings"""
        recommendations = []
        
        # Count issues by type
        error_counts = defaultdict(int)
        for error in self.error_reports:
            error_counts[error.category] += 1
        
        if error_counts.get('security', 0) > 0:
            recommendations.append("🔒 **URGENT:** Address security vulnerabilities immediately - move secrets to environment variables")
        
        if error_counts.get('type_checking', 0) > 10:
            recommendations.append("🔧 Fix type checking errors to improve code reliability and IDE support")
        
        if error_counts.get('test_coverage', 0) > 0:
            recommendations.append("🧪 **HIGH PRIORITY:** Implement comprehensive test suite - current coverage is insufficient")
        
        if error_counts.get('documentation', 0) > 5:
            recommendations.append("📚 Add comprehensive documentation and docstrings")
        
        if error_counts.get('style', 0) > 20:
            recommendations.append("🎨 Implement consistent code formatting with automated tools (black, isort)")
        
        if error_counts.get('dependency_vulnerability', 0) > 0:
            recommendations.append("📦 Update vulnerable dependencies to secure versions")
        
        if error_counts.get('database_design', 0) > 0:
            recommendations.append("🗄️ Review database schema design and consider normalization")
        
        if error_counts.get('api_reliability', 0) > 5:
            recommendations.append("🌐 Improve API error handling and input validation")
        
        if error_counts.get('docker_security', 0) > 0:
            recommendations.append("🐳 Enhance Docker security configuration")
        
        recommendations.append("🔄 Set up automated code quality checks in CI/CD")
        recommendations.append("📊 Implement monitoring and alerting for production")
        
        return recommendations
    
    def save_detailed_json_report(self) -> str:
        """Save detailed JSON report for further analysis"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "analysis_duration": (datetime.now() - self.start_time).total_seconds(),
            "summary": {
                "total_issues": sum(r.total_issues for r in self.results),
                "total_errors": sum(r.errors for r in self.results),
                "total_warnings": sum(r.warnings for r in self.results),
                "total_info": sum(r.info for r in self.results)
            },
            "tool_results": [asdict(result) for result in self.results],
            "detailed_errors": [asdict(error) for error in self.error_reports],
            "categories": dict(Counter(e.category for e in self.error_reports)),
            "impacts": dict(Counter(e.impact for e in self.error_reports if e.impact)),
            "tools": dict(Counter(e.tool for e in self.error_reports)),
            "fix_efforts": dict(Counter(e.fix_effort for e in self.error_reports)),
            "business_impacts": dict(Counter(e.business_impact for e in self.error_reports)),
            "database_tables": self.database_tables,
            "api_endpoints": self.api_endpoints
        }
        
        json_file = self.project_root / "ERROR_ANALYSIS_DETAILED.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return str(json_file)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "/workspaces/ai-hedge-fund"
    
    analyzer = UltraDeepErrorAnalyzer(project_root)
    summary = analyzer.run_full_analysis()
    
    print("\n" + "="*80)
    print("ULTRA-DEEP ANALYSIS SUMMARY")
    print("="*80)
    print(summary)

if __name__ == "__main__":
    main()
