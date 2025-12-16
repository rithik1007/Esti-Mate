import os
import ast
import json
import re
from typing import Dict, List, Any
from pathlib import Path

class CodebaseAnalyzer:
    def __init__(self):
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go'
        }
    
    def analyze_codebase(self, repo_path: str) -> Dict:
        """Analyze entire codebase to understand patterns and structure"""
        
        if not os.path.exists(repo_path):
            return {"error": "Repository path not found"}
        
        analysis = {
            "tech_stack": self._detect_tech_stack(repo_path),
            "architecture_pattern": self._detect_architecture_pattern(repo_path),
            "code_patterns": self._analyze_code_patterns(repo_path),
            "database_schema": self._analyze_database_schema(repo_path),
            "api_patterns": self._analyze_api_patterns(repo_path),
            "test_patterns": self._analyze_test_patterns(repo_path),
            "component_patterns": self._analyze_component_patterns(repo_path),
            "coding_standards": self._analyze_coding_standards(repo_path),
            "dependencies": self._analyze_dependencies(repo_path)
        }
        
        return analysis
    
    def _detect_tech_stack(self, repo_path: str) -> Dict:
        """Detect technologies used in the codebase"""
        
        tech_stack = {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "frontend_framework": None,
            "backend_framework": None,
            "test_framework": None
        }
        
        # Check package.json for Node.js projects
        package_json = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    # Frontend frameworks
                    if 'react' in deps:
                        tech_stack["frontend_framework"] = "React"
                    elif 'vue' in deps:
                        tech_stack["frontend_framework"] = "Vue"
                    elif 'angular' in deps or '@angular/core' in deps:
                        tech_stack["frontend_framework"] = "Angular"
                    
                    # Backend frameworks
                    if 'express' in deps:
                        tech_stack["backend_framework"] = "Express"
                    elif 'next' in deps:
                        tech_stack["backend_framework"] = "Next.js"
                    
                    # Test frameworks
                    if 'jest' in deps:
                        tech_stack["test_framework"] = "Jest"
                    elif 'mocha' in deps:
                        tech_stack["test_framework"] = "Mocha"
                    elif 'cypress' in deps:
                        tech_stack["test_framework"] = "Cypress"
                    
                    tech_stack["languages"].append("JavaScript")
                    
            except Exception as e:
                pass
        
        # Check requirements.txt for Python projects
        requirements_txt = os.path.join(repo_path, 'requirements.txt')
        if os.path.exists(requirements_txt):
            try:
                with open(requirements_txt, 'r') as f:
                    content = f.read().lower()
                    
                    if 'django' in content:
                        tech_stack["backend_framework"] = "Django"
                    elif 'flask' in content:
                        tech_stack["backend_framework"] = "Flask"
                    elif 'fastapi' in content:
                        tech_stack["backend_framework"] = "FastAPI"
                    
                    if 'pytest' in content:
                        tech_stack["test_framework"] = "pytest"
                    
                    tech_stack["languages"].append("Python")
                    
            except Exception as e:
                pass
        
        # Check pom.xml for Java projects
        pom_xml = os.path.join(repo_path, 'pom.xml')
        if os.path.exists(pom_xml):
            tech_stack["languages"].append("Java")
            tech_stack["backend_framework"] = "Spring Boot"  # Common assumption
        
        # Scan for file extensions
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self.supported_extensions:
                    lang = self.supported_extensions[ext]
                    if lang not in tech_stack["languages"]:
                        tech_stack["languages"].append(lang)
        
        return tech_stack
    
    def _detect_architecture_pattern(self, repo_path: str) -> str:
        """Detect architectural patterns used"""
        
        patterns = []
        
        # Check directory structure
        dirs = [d for d in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, d))]
        
        # MVC pattern
        if any(d in ['models', 'views', 'controllers'] for d in dirs):
            patterns.append("MVC")
        
        # Microservices
        if any(d in ['services', 'microservices'] for d in dirs):
            patterns.append("Microservices")
        
        # Layered architecture
        if any(d in ['service', 'repository', 'dao', 'entity'] for d in dirs):
            patterns.append("Layered")
        
        # Component-based (React/Vue)
        if any(d in ['components', 'pages', 'layouts'] for d in dirs):
            patterns.append("Component-based")
        
        return ", ".join(patterns) if patterns else "Standard"
    
    def _analyze_code_patterns(self, repo_path: str) -> Dict:
        """Analyze common code patterns and conventions"""
        
        patterns = {
            "naming_convention": "camelCase",  # Default
            "class_patterns": [],
            "function_patterns": [],
            "import_patterns": []
        }
        
        # Sample a few files to understand patterns
        sample_files = self._get_sample_files(repo_path, limit=10)
        
        for file_path in sample_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Analyze naming conventions
                    if re.search(r'class [A-Z][a-zA-Z]*', content):
                        patterns["naming_convention"] = "PascalCase"
                    elif re.search(r'function [a-z][a-zA-Z]*', content):
                        patterns["naming_convention"] = "camelCase"
                    elif re.search(r'def [a-z_]+', content):
                        patterns["naming_convention"] = "snake_case"
                    
                    # Extract class patterns
                    class_matches = re.findall(r'class\s+(\w+)', content)
                    patterns["class_patterns"].extend(class_matches[:3])
                    
                    # Extract function patterns
                    func_matches = re.findall(r'(?:function|def)\s+(\w+)', content)
                    patterns["function_patterns"].extend(func_matches[:5])
                    
            except Exception as e:
                continue
        
        return patterns
    
    def _analyze_database_schema(self, repo_path: str) -> Dict:
        """Analyze database schema and models"""
        
        schema_info = {
            "models": [],
            "migrations": [],
            "database_type": "Unknown"
        }
        
        # Look for model files
        model_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if 'model' in file.lower() or 'entity' in file.lower():
                    model_files.append(os.path.join(root, file))
        
        # Analyze model files
        for model_file in model_files[:5]:  # Limit to 5 files
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Extract model names
                    model_matches = re.findall(r'class\s+(\w+)', content)
                    schema_info["models"].extend(model_matches)
                    
            except Exception as e:
                continue
        
        return schema_info
    
    def _analyze_api_patterns(self, repo_path: str) -> Dict:
        """Analyze API patterns and endpoints"""
        
        api_patterns = {
            "rest_endpoints": [],
            "route_patterns": [],
            "middleware_patterns": []
        }
        
        # Look for route/controller files
        route_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(keyword in file.lower() for keyword in ['route', 'controller', 'api', 'endpoint']):
                    route_files.append(os.path.join(root, file))
        
        # Analyze route patterns
        for route_file in route_files[:5]:
            try:
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Extract route patterns
                    route_matches = re.findall(r'@app\.route\([\'"]([^\'"]+)[\'"]', content)
                    api_patterns["rest_endpoints"].extend(route_matches)
                    
                    # Express.js patterns
                    express_matches = re.findall(r'app\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]', content)
                    api_patterns["rest_endpoints"].extend([match[1] for match in express_matches])
                    
            except Exception as e:
                continue
        
        return api_patterns
    
    def _analyze_test_patterns(self, repo_path: str) -> Dict:
        """Analyze testing patterns and structure"""
        
        test_patterns = {
            "test_files": [],
            "test_structure": "Unknown",
            "assertion_patterns": []
        }
        
        # Find test files
        test_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if 'test' in file.lower() or file.endswith('.spec.js') or file.endswith('_test.py'):
                    test_files.append(os.path.join(root, file))
        
        test_patterns["test_files"] = [os.path.basename(f) for f in test_files[:10]]
        
        # Analyze test structure
        if any('__tests__' in f for f in test_files):
            test_patterns["test_structure"] = "Jest/__tests__"
        elif any('tests/' in f for f in test_files):
            test_patterns["test_structure"] = "tests/ directory"
        
        return test_patterns
    
    def _analyze_component_patterns(self, repo_path: str) -> Dict:
        """Analyze frontend component patterns"""
        
        component_patterns = {
            "component_structure": "Unknown",
            "component_names": [],
            "styling_approach": "Unknown"
        }
        
        # Look for component files
        component_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.jsx', '.tsx', '.vue')) or 'component' in file.lower():
                    component_files.append(os.path.join(root, file))
        
        # Analyze component structure
        if component_files:
            component_patterns["component_names"] = [os.path.basename(f) for f in component_files[:10]]
            
            # Check styling approach
            if any(f.endswith('.module.css') for f in os.listdir(repo_path) if os.path.isfile(os.path.join(repo_path, f))):
                component_patterns["styling_approach"] = "CSS Modules"
            elif any('styled-components' in str(f) for f in component_files):
                component_patterns["styling_approach"] = "Styled Components"
        
        return component_patterns
    
    def _analyze_coding_standards(self, repo_path: str) -> Dict:
        """Analyze coding standards and conventions"""
        
        standards = {
            "linting": "Unknown",
            "formatting": "Unknown",
            "code_style": "Unknown"
        }
        
        # Check for linting configs
        if os.path.exists(os.path.join(repo_path, '.eslintrc.js')) or os.path.exists(os.path.join(repo_path, '.eslintrc.json')):
            standards["linting"] = "ESLint"
        elif os.path.exists(os.path.join(repo_path, 'pylint.cfg')) or os.path.exists(os.path.join(repo_path, '.pylintrc')):
            standards["linting"] = "Pylint"
        
        # Check for formatting configs
        if os.path.exists(os.path.join(repo_path, '.prettierrc')):
            standards["formatting"] = "Prettier"
        elif os.path.exists(os.path.join(repo_path, 'pyproject.toml')):
            standards["formatting"] = "Black"
        
        return standards
    
    def _analyze_dependencies(self, repo_path: str) -> Dict:
        """Analyze project dependencies"""
        
        dependencies = {
            "package_manager": "Unknown",
            "key_dependencies": [],
            "dev_dependencies": []
        }
        
        # Node.js dependencies
        package_json = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json):
            dependencies["package_manager"] = "npm/yarn"
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    dependencies["key_dependencies"] = list(data.get('dependencies', {}).keys())[:10]
                    dependencies["dev_dependencies"] = list(data.get('devDependencies', {}).keys())[:10]
            except:
                pass
        
        # Python dependencies
        requirements_txt = os.path.join(repo_path, 'requirements.txt')
        if os.path.exists(requirements_txt):
            dependencies["package_manager"] = "pip"
            try:
                with open(requirements_txt, 'r') as f:
                    deps = [line.split('==')[0].strip() for line in f.readlines() if line.strip()]
                    dependencies["key_dependencies"] = deps[:10]
            except:
                pass
        
        return dependencies
    
    def _get_sample_files(self, repo_path: str, limit: int = 10) -> List[str]:
        """Get sample files for analysis"""
        
        sample_files = []
        count = 0
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv']]
            
            for file in files:
                if count >= limit:
                    break
                    
                ext = os.path.splitext(file)[1].lower()
                if ext in self.supported_extensions:
                    sample_files.append(os.path.join(root, file))
                    count += 1
        
        return sample_files
    
    def get_code_samples(self, repo_path: str, file_types: List[str] = None) -> Dict:
        """Get code samples for AI training"""
        
        if file_types is None:
            file_types = ['.py', '.js', '.jsx', '.ts', '.tsx']
        
        code_samples = {}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in file_types:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if len(content) < 5000:  # Only small files
                                code_samples[file] = content[:1000]  # First 1000 chars
                    except:
                        continue
                    
                    if len(code_samples) >= 20:  # Limit samples
                        break
        
        return code_samples