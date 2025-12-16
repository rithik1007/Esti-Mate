import openai
import json
from typing import Dict, List, Any

class SolutionDesigner:
    def __init__(self, api_key: str = None, azure_endpoint: str = None):
        self.api_key = api_key
        self.azure_endpoint = azure_endpoint
        
        if api_key and azure_endpoint:
            openai.api_type = "azure"
            openai.api_base = azure_endpoint
            openai.api_version = "2024-02-15-preview"
            openai.api_key = api_key
    
    def generate_solution_design(self, ticket_data: Dict, codebase_context: Dict) -> Dict:
        """Generate comprehensive solution design for a JIRA ticket"""
        
        prompt = self._build_design_prompt(ticket_data, codebase_context)
        
        try:
            response = openai.ChatCompletion.create(
                engine="gpt-5.1-chat",
                messages=[
                    {"role": "system", "content": "You are a senior software architect. Generate detailed technical designs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            design_content = response.choices[0].message.content
            return self._parse_design_response(design_content)
            
        except Exception as e:
            return self._fallback_design(ticket_data, codebase_context)
    
    def _build_design_prompt(self, ticket_data: Dict, codebase_context: Dict) -> str:
        return f"""
        Create a detailed solution design for this ticket:
        
        **Ticket Details:**
        - Summary: {ticket_data.get('summary', '')}
        - Description: {ticket_data.get('description', '')}
        - Type: {ticket_data.get('issue_type', '')}
        - Priority: {ticket_data.get('priority', '')}
        
        **Codebase Context:**
        - Tech Stack: {codebase_context.get('tech_stack', [])}
        - Architecture: {codebase_context.get('architecture_pattern', '')}
        - Existing Components: {codebase_context.get('components', [])}
        
        Generate a design with:
        1. **Solution Overview** - High-level approach
        2. **Technical Architecture** - Components and interactions
        3. **Implementation Plan** - Step-by-step breakdown
        4. **Database Changes** - Schema modifications if needed
        5. **API Design** - Endpoints and contracts
        6. **Testing Strategy** - Unit, integration, and E2E tests
        7. **Risk Assessment** - Potential challenges and mitigation
        8. **Acceptance Criteria** - Measurable success criteria
        
        Format as JSON with clear sections.
        """
    
    def _parse_design_response(self, content: str) -> Dict:
        """Parse AI response into structured design"""
        try:
            # Try to extract JSON from response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(content[start:end])
        except:
            pass
        
        # Fallback: structure the text response
        return {
            "solution_overview": self._extract_section(content, "Solution Overview"),
            "technical_architecture": self._extract_section(content, "Technical Architecture"),
            "implementation_plan": self._extract_section(content, "Implementation Plan"),
            "database_changes": self._extract_section(content, "Database Changes"),
            "api_design": self._extract_section(content, "API Design"),
            "testing_strategy": self._extract_section(content, "Testing Strategy"),
            "risk_assessment": self._extract_section(content, "Risk Assessment"),
            "acceptance_criteria": self._extract_section(content, "Acceptance Criteria"),
            "raw_content": content
        }
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract specific section from text"""
        lines = content.split('\n')
        section_content = []
        in_section = False
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                continue
            elif in_section and line.strip().startswith(('##', '**', '1.', '2.', '3.')):
                break
            elif in_section:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _fallback_design(self, ticket_data: Dict, codebase_context: Dict) -> Dict:
        """Generate basic design when AI is unavailable"""
        return {
            "solution_overview": f"Implement {ticket_data.get('summary', 'feature')} using existing {codebase_context.get('tech_stack', ['framework'])}",
            "technical_architecture": "Follow existing architecture patterns in the codebase",
            "implementation_plan": [
                "1. Analyze existing code structure",
                "2. Create necessary components",
                "3. Implement business logic",
                "4. Add tests",
                "5. Update documentation"
            ],
            "database_changes": "TBD - Analyze if schema changes needed",
            "api_design": "Follow existing API patterns",
            "testing_strategy": "Unit tests, integration tests, manual testing",
            "risk_assessment": "Medium complexity - follow existing patterns",
            "acceptance_criteria": ticket_data.get('description', 'Feature works as described'),
            "status": "fallback_generated"
        }

class DesignApprovalWorkflow:
    def __init__(self):
        self.pending_designs = {}
        self.approved_designs = {}
    
    def submit_for_approval(self, ticket_key: str, design: Dict, approvers: List[str]) -> str:
        """Submit design for approval"""
        approval_id = f"design_{ticket_key}_{len(self.pending_designs)}"
        
        self.pending_designs[approval_id] = {
            "ticket_key": ticket_key,
            "design": design,
            "approvers": approvers,
            "status": "pending",
            "submitted_at": json.dumps({"timestamp": "now"}),
            "comments": []
        }
        
        return approval_id
    
    def add_approval_comment(self, approval_id: str, approver: str, comment: str, approved: bool):
        """Add approval comment"""
        if approval_id in self.pending_designs:
            self.pending_designs[approval_id]["comments"].append({
                "approver": approver,
                "comment": comment,
                "approved": approved,
                "timestamp": "now"
            })
    
    def approve_design(self, approval_id: str, approver: str) -> bool:
        """Approve a design"""
        if approval_id in self.pending_designs:
            design_data = self.pending_designs[approval_id]
            design_data["status"] = "approved"
            design_data["approved_by"] = approver
            
            self.approved_designs[approval_id] = design_data
            del self.pending_designs[approval_id]
            return True
        return False
    
    def get_pending_designs(self) -> Dict:
        """Get all pending designs"""
        return self.pending_designs
    
    def get_approved_design(self, approval_id: str) -> Dict:
        """Get approved design"""
        return self.approved_designs.get(approval_id)