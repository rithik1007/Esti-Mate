import boto3
import json
from typing import Dict, Any

class AmazonQEstimator:
    def __init__(self, aws_region: str = None, aws_access_key: str = None, 
                 aws_secret_key: str = None, app_id: str = None):
        self.aws_region = aws_region or 'us-east-1'
        self.app_id = app_id
        self.client = None
        
        if aws_access_key and aws_secret_key:
            try:
                self.client = boto3.client(
                    'qbusiness',
                    region_name=self.aws_region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
                print(f"DEBUG - Amazon Q client initialized for region: {self.aws_region}")
            except Exception as e:
                print(f"DEBUG - Failed to initialize Amazon Q client: {e}")
                self.client = None
    
    def estimate_with_amazon_q(self, description: str, jira_data: Dict = None, 
                               codebase_context: str = None) -> Dict:
        """Use Amazon Q to estimate project complexity and hours"""
        
        if not self.client or not self.app_id:
            print("DEBUG - Amazon Q not configured, using fallback")
            return None
        
        try:
            # Build context for Amazon Q
            context = self._build_estimation_context(description, jira_data, codebase_context)
            
            # Call Amazon Q
            response = self.client.chat_sync(
                applicationId=self.app_id,
                userMessage=context,
                conversationId=None  # New conversation
            )
            
            # Parse response
            if 'systemMessage' in response:
                ai_response = response['systemMessage']
                return self._parse_amazon_q_response(ai_response)
            
            return None
            
        except Exception as e:
            print(f"DEBUG - Amazon Q estimation failed: {str(e)}")
            return None
    
    def _build_estimation_context(self, description: str, jira_data: Dict = None, 
                                  codebase_context: str = None) -> str:
        """Build context for Amazon Q estimation"""
        
        context = f"""
You are a senior software architect estimating development tasks. Analyze the following and provide a realistic time estimate.

**Task Description:**
{description}
"""
        
        if jira_data:
            context += f"""

**JIRA Details:**
- Issue Type: {jira_data.get('issue_type', 'Unknown')}
- Priority: {jira_data.get('priority', 'Medium')}
- Status: {jira_data.get('status', 'Unknown')}
- Summary: {jira_data.get('summary', '')}
"""
            
            if jira_data.get('linked_issues'):
                linked_info = [f"{link['key']} ({link['type']})" for link in jira_data['linked_issues']]
                context += f"\n- Linked Issues: {', '.join(linked_info)}"
            
            if jira_data.get('status_history'):
                context += f"\n- Historical Status Changes: {len(jira_data['status_history'])} transitions"
            
            if jira_data.get('time_in_status'):
                context += "\n- Time Spent in Statuses:"
                for status, hours in jira_data['time_in_status'].items():
                    context += f"\n  * {status}: {hours:.1f} hours"
        
        if codebase_context:
            context += f"""

**Codebase Context:**
{codebase_context}
"""
        
        context += """

**Estimation Guidelines:**
- React Native upgrades: 120-400 hours depending on version jump
- Enterprise integrations (IIB, SAP): 80-120 hours base
- Security updates (BlackDuck): 32 hours max
- Standard CRUD operations: 40-80 hours
- Complex features: 80-160 hours

**Provide estimation in JSON format:**
{
    "total_hours": <number>,
    "complexity": "<Low|Medium|High>",
    "confidence": <number 50-95>,
    "reasoning": "<detailed explanation>",
    "risk_factors": ["<factor1>", "<factor2>"],
    "phases": {
        "requirements": <hours>,
        "design": <hours>,
        "development": <hours>,
        "testing": <hours>,
        "deployment": <hours>
    }
}
"""
        
        return context
    
    def _parse_amazon_q_response(self, response: str) -> Dict:
        """Parse Amazon Q response into structured estimation"""
        
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                estimation = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['total_hours', 'complexity', 'phases']
                if all(field in estimation for field in required_fields):
                    estimation['estimation_method'] = 'amazon_q'
                    return estimation
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"DEBUG - Failed to parse Amazon Q JSON: {e}")
        
        # Fallback: extract key information
        return self._extract_estimation_manually(response)
    
    def _extract_estimation_manually(self, response: str) -> Dict:
        """Manually extract estimation from Amazon Q response"""
        
        import re
        
        # Try to find total hours
        hour_patterns = [
            r'total[_\s]*hours?[:\s]*(\d+)',
            r'(\d+)[_\s]*hours?\\s*total',
            r'estimate[:\s]*(\d+)[_\s]*hours?'
        ]
        
        total_hours = 80  # Default
        for pattern in hour_patterns:
            match = re.search(pattern, response.lower())
            if match:
                total_hours = int(match.group(1))
                break
        
        # Determine complexity
        if total_hours >= 120:
            complexity = 'High'
        elif total_hours >= 60:
            complexity = 'Medium'
        else:
            complexity = 'Low'
        
        # Default phase distribution
        phases = {
            'requirements': round(total_hours * 0.15, 1),
            'design': round(total_hours * 0.20, 1),
            'development': round(total_hours * 0.48, 1),
            'testing': round(total_hours * 0.15, 1),
            'deployment': round(total_hours * 0.02, 1)
        }
        
        return {
            'total_hours': total_hours,
            'complexity': complexity,
            'reasoning': 'Extracted from Amazon Q response',
            'phases': phases,
            'estimation_method': 'amazon_q_extracted',
            'confidence': 80
        }
