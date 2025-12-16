import openai
import os
import ast
from typing import Dict, List, Any
from ..repo_analyzer.codebase_analyzer import CodebaseAnalyzer

class AICodeGenerator:
    def __init__(self, api_key: str = None, azure_endpoint: str = None):
        self.api_key = api_key
        self.azure_endpoint = azure_endpoint
        
        if api_key and azure_endpoint:
            openai.api_type = "azure"
            openai.api_base = azure_endpoint
            openai.api_version = "2024-02-15-preview"
            openai.api_key = api_key
        self.analyzer = CodebaseAnalyzer()
    
    def generate_code_from_design(self, design: Dict, codebase_path: str, ticket_data: Dict) -> Dict:
        """Generate code snippets based on approved design"""
        
        # Analyze existing codebase
        codebase_context = self.analyzer.analyze_codebase(codebase_path)
        
        # Generate different types of code
        generated_code = {
            "backend_code": self._generate_backend_code(design, codebase_context, ticket_data),
            "frontend_code": self._generate_frontend_code(design, codebase_context, ticket_data),
            "database_scripts": self._generate_database_scripts(design, codebase_context),
            "test_code": self._generate_test_code(design, codebase_context, ticket_data),
            "api_documentation": self._generate_api_docs(design, codebase_context)
        }
        
        return generated_code
    
    def _generate_backend_code(self, design: Dict, codebase_context: Dict, ticket_data: Dict) -> Dict:
        """Generate backend code following codebase patterns"""
        
        tech_stack = codebase_context.get('tech_stack', {})
        patterns = codebase_context.get('patterns', {})
        
        prompt = f"""
        Generate backend code for this feature:
        
        **Design:** {design.get('solution_overview', '')}
        **Implementation Plan:** {design.get('implementation_plan', '')}
        **API Design:** {design.get('api_design', '')}
        
        **Codebase Context:**
        - Framework: {tech_stack.get('backend_framework', 'Unknown')}
        - Database: {tech_stack.get('database', 'Unknown')}
        - Patterns: {patterns}
        
        **Existing Code Style:**
        {codebase_context.get('code_samples', '')}
        
        Generate:
        1. Controller/Route handlers
        2. Service layer classes
        3. Data models/entities
        4. Repository/DAO classes
        5. Validation logic
        
        Follow the existing code style and patterns exactly.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert developer. Generate production-ready code following existing patterns."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            return self._parse_code_response(response.choices[0].message.content, 'backend')
            
        except Exception as e:
            return self._generate_fallback_backend_code(design, codebase_context)
    
    def _generate_frontend_code(self, design: Dict, codebase_context: Dict, ticket_data: Dict) -> Dict:
        """Generate frontend code components"""
        
        tech_stack = codebase_context.get('tech_stack', {})
        
        prompt = f"""
        Generate frontend code for:
        
        **Feature:** {ticket_data.get('summary', '')}
        **UI Requirements:** {design.get('solution_overview', '')}
        
        **Tech Stack:**
        - Framework: {tech_stack.get('frontend_framework', 'React')}
        - Styling: {tech_stack.get('css_framework', 'CSS')}
        
        **Existing Component Patterns:**
        {codebase_context.get('component_patterns', '')}
        
        Generate:
        1. Main component
        2. Sub-components if needed
        3. Styling (CSS/SCSS)
        4. API integration code
        5. Form validation
        
        Follow existing naming conventions and patterns.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate clean, reusable frontend components following best practices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            return self._parse_code_response(response.choices[0].message.content, 'frontend')
            
        except Exception as e:
            return self._generate_fallback_frontend_code(design, codebase_context)
    
    def _generate_database_scripts(self, design: Dict, codebase_context: Dict) -> Dict:
        """Generate database migration scripts"""
        
        db_changes = design.get('database_changes', '')
        if not db_changes or 'no changes' in db_changes.lower():
            return {"migrations": [], "message": "No database changes required"}
        
        db_type = codebase_context.get('tech_stack', {}).get('database', 'PostgreSQL')
        
        prompt = f"""
        Generate database migration scripts for:
        
        **Database Changes:** {db_changes}
        **Database Type:** {db_type}
        **Existing Schema:** {codebase_context.get('database_schema', '')}
        
        Generate:
        1. Migration up script
        2. Migration down script (rollback)
        3. Index creation if needed
        4. Data migration if required
        
        Follow existing migration patterns.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"Generate {db_type} migration scripts following best practices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            return self._parse_code_response(response.choices[0].message.content, 'database')
            
        except Exception as e:
            return {"error": str(e), "fallback": "Manual database script creation required"}
    
    def _generate_test_code(self, design: Dict, codebase_context: Dict, ticket_data: Dict) -> Dict:
        """Generate comprehensive test suite"""
        
        testing_strategy = design.get('testing_strategy', '')
        test_framework = codebase_context.get('tech_stack', {}).get('test_framework', 'Jest')
        
        prompt = f"""
        Generate test code for:
        
        **Feature:** {ticket_data.get('summary', '')}
        **Testing Strategy:** {testing_strategy}
        **Test Framework:** {test_framework}
        
        **Existing Test Patterns:**
        {codebase_context.get('test_patterns', '')}
        
        Generate:
        1. Unit tests for business logic
        2. Integration tests for APIs
        3. Component tests for UI
        4. E2E test scenarios
        5. Mock data and fixtures
        
        Follow existing test structure and naming.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate comprehensive test suites with good coverage."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            return self._parse_code_response(response.choices[0].message.content, 'tests')
            
        except Exception as e:
            return self._generate_fallback_test_code(design, codebase_context)
    
    def _generate_api_docs(self, design: Dict, codebase_context: Dict) -> Dict:
        """Generate API documentation"""
        
        api_design = design.get('api_design', '')
        if not api_design:
            return {"message": "No API changes documented"}
        
        prompt = f"""
        Generate API documentation for:
        
        **API Design:** {api_design}
        **Documentation Format:** {codebase_context.get('doc_format', 'OpenAPI')}
        
        Generate:
        1. Endpoint specifications
        2. Request/Response schemas
        3. Error codes and messages
        4. Usage examples
        5. Authentication requirements
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Generate clear, comprehensive API documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            return {"documentation": response.choices[0].message.content}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_code_response(self, content: str, code_type: str) -> Dict:
        """Parse AI response into structured code snippets"""
        
        code_blocks = []
        lines = content.split('\n')
        current_block = None
        
        for line in lines:
            if line.strip().startswith('```'):
                if current_block is None:
                    # Start new code block
                    language = line.strip()[3:].strip()
                    current_block = {
                        "language": language,
                        "code": [],
                        "filename": ""
                    }
                else:
                    # End current code block
                    current_block["code"] = '\n'.join(current_block["code"])
                    code_blocks.append(current_block)
                    current_block = None
            elif current_block is not None:
                current_block["code"].append(line)
            elif line.strip().startswith('//') and 'filename:' in line.lower():
                # Extract filename from comment
                if code_blocks:
                    filename = line.split('filename:')[-1].strip()
                    code_blocks[-1]["filename"] = filename
        
        return {
            "code_blocks": code_blocks,
            "raw_content": content,
            "type": code_type
        }
    
    def _generate_fallback_backend_code(self, design: Dict, codebase_context: Dict) -> Dict:
        """Generate basic backend code template"""
        return {
            "code_blocks": [{
                "language": "python",
                "filename": "feature_service.py",
                "code": f"""
# Generated service class for {design.get('solution_overview', 'feature')}
class FeatureService:
    def __init__(self):
        pass
    
    def process_request(self, data):
        # TODO: Implement business logic
        return {{"status": "success", "data": data}}
"""
            }],
            "type": "backend",
            "status": "fallback_generated"
        }
    
    def _generate_fallback_frontend_code(self, design: Dict, codebase_context: Dict) -> Dict:
        """Generate basic frontend code template"""
        return {
            "code_blocks": [{
                "language": "javascript",
                "filename": "FeatureComponent.jsx",
                "code": f"""
// Generated component for {design.get('solution_overview', 'feature')}
import React from 'react';

const FeatureComponent = () => {{
    return (
        <div>
            <h2>New Feature</h2>
            {{/* TODO: Implement UI */}}
        </div>
    );
}};

export default FeatureComponent;
"""
            }],
            "type": "frontend",
            "status": "fallback_generated"
        }
    
    def _generate_fallback_test_code(self, design: Dict, codebase_context: Dict) -> Dict:
        """Generate basic test template"""
        return {
            "code_blocks": [{
                "language": "javascript",
                "filename": "feature.test.js",
                "code": f"""
// Generated tests for {design.get('solution_overview', 'feature')}
describe('Feature Tests', () => {{
    test('should implement feature correctly', () => {{
        // TODO: Add test cases
        expect(true).toBe(true);
    }});
}});
"""
            }],
            "type": "tests",
            "status": "fallback_generated"
        }