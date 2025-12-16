from openai import AzureOpenAI
import json
import os
from typing import Dict, Any

class AIEstimator:
    def __init__(self, api_key: str = None, azure_endpoint: str = None):
        self.api_key = api_key
        self.azure_endpoint = azure_endpoint
        self.client = None
        
        if api_key and azure_endpoint:
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=azure_endpoint
            )
    
    def estimate_with_ai(self, description: str, jira_data: Dict = None) -> Dict:
        """Use AI to estimate project complexity and hours"""
        
        print(f"DEBUG - AI Estimator called with API key: {bool(self.api_key)}")
        print(f"DEBUG - Azure endpoint: {self.azure_endpoint}")
        
        if not self.api_key:
            print("DEBUG - No API key, using fallback estimation")
            # Fallback to rule-based estimation
            return self._fallback_estimation(description, jira_data)
        
        try:
            print("DEBUG - Calling FAB API for estimation...")
            # Prepare context for AI
            context = self._build_estimation_context(description, jira_data)
            
            # Get AI estimation
            ai_response = self._get_ai_estimation(context)
            print(f"DEBUG - AI Response received: {ai_response[:200]}...")
            
            # Parse and validate AI response
            estimation = self._parse_ai_response(ai_response)
            
            return estimation
            
        except Exception as e:
            print(f"DEBUG - AI estimation failed: {str(e)}")
            print(f"DEBUG - Falling back to rule-based estimation")
            # Fallback to rule-based estimation
            return self._fallback_estimation(description, jira_data)
    
    def _build_estimation_context(self, description: str, jira_data: Dict = None) -> str:
        """Build context for AI estimation"""
        
        context = f"""
        You are a senior React Native architect estimating complex mobile development tasks. Be realistic about time requirements.
        
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
        
        context += """
        
        **CRITICAL ESTIMATION RULES:**
        
        **React Native Version Upgrades (ALWAYS HIGH COMPLEXITY):**
        - Minor version (0.76.x to 0.77.x): 120-200 hours
        - Major version (0.76.x to 0.79.x): 200-400 hours
        - Breaking changes analysis: 40-80 hours
        - Third-party library compatibility fixes: 60-150 hours
        - Native module updates: 80-200 hours
        - Testing across devices/platforms: 100-200 hours
        
        **iOS Native Work:**
        - Objective-C to Swift migration: 80-200 hours per major module
        - Native iOS dependency updates: 60-120 hours
        - iOS-specific breaking changes: 40-100 hours
        
        **Android Native Work:**
        - Native Android dependency updates: 60-150 hours
        - Gradle/build system updates: 40-80 hours
        - Android-specific breaking changes: 40-100 hours
        
        **Combined React Native + Native Migration:**
        - If description mentions BOTH React Native upgrade AND native language migration: MINIMUM 250 hours
        - Add 50-100% buffer for unexpected compatibility issues
        - Always mark as HIGH complexity
        
        **Keywords that indicate HIGH complexity (200+ hours):**
        - "React Native upgrade" + version numbers
        - "Objective-C to Swift"
        - "native dependencies"
        - "third party dependencies"
        - "breaking changes"
        - "migration"
        
        **Response Format (JSON):**
        {
            "total_hours": <number - BE REALISTIC, err on higher side>,
            "complexity": "<Low|Medium|High>",
            "confidence": <0-100>,
            "reasoning": "<detailed explanation of why this estimate>",
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
    
    def _get_ai_estimation(self, context: str) -> str:
        """Get estimation from Azure OpenAI"""
        
        response = self.client.chat.completions.create(
            model="gpt-5-1-chat-2025-11-13",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a senior software architect and project manager with 15+ years of experience in estimating software development tasks. Provide accurate, realistic estimates based on industry standards."
                },
                {
                    "role": "user", 
                    "content": context
                }
            ],
            max_completion_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def _parse_ai_response(self, ai_response: str) -> Dict:
        """Parse AI response into structured estimation"""
        
        try:
            # Try to extract JSON from response
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = ai_response[start:end]
                estimation = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['total_hours', 'complexity', 'phases']
                if all(field in estimation for field in required_fields):
                    # Add metadata
                    estimation['estimation_method'] = 'ai_powered'
                    estimation['ai_confidence'] = estimation.get('confidence', 75)
                    
                    return estimation
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse AI response: {e}")
        
        # If parsing fails, extract key information manually
        return self._extract_estimation_manually(ai_response)
    
    def _extract_estimation_manually(self, ai_response: str) -> Dict:
        """Manually extract estimation from AI response"""
        
        # Look for hour estimates in the text
        import re
        
        # Try to find total hours
        hour_patterns = [
            r'total[_\s]*hours?[:\s]*(\d+)',
            r'(\d+)[_\s]*hours?\s*total',
            r'estimate[:\s]*(\d+)[_\s]*hours?'
        ]
        
        total_hours = 80  # Default
        for pattern in hour_patterns:
            match = re.search(pattern, ai_response.lower())
            if match:
                total_hours = int(match.group(1))
                break
        
        # Determine complexity based on hours
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
            'development': round(total_hours * 0.45, 1),
            'testing': round(total_hours * 0.15, 1),
            'deployment': round(total_hours * 0.05, 1)
        }
        
        return {
            'total_hours': total_hours,
            'complexity': complexity,
            'confidence': 70,
            'reasoning': 'Extracted from AI response text',
            'phases': phases,
            'estimation_method': 'ai_extracted',
            'ai_response': ai_response[:500]  # First 500 chars for debugging
        }
    
    def _fallback_estimation(self, description: str, jira_data: Dict = None) -> Dict:
        """Fallback rule-based estimation when AI is unavailable"""
        
        description_lower = description.lower()
        complexity_score = 0
        
        # Enhanced keyword analysis for React Native
        high_keywords = [
            'react native', 'upgrade', 'migration', 'objective-c', 'swift', 
            'native dependencies', 'third party', 'breaking changes', 
            'integration', 'api', 'database', 'security', 'authentication'
        ]
        medium_keywords = [
            'crud', 'form', 'validation', 'report', 'dashboard',
            'ui', 'frontend', 'backend', 'update', 'dependency'
        ]
        
        high_count = sum(1 for keyword in high_keywords if keyword in description_lower)
        medium_count = sum(1 for keyword in medium_keywords if keyword in description_lower)
        
        complexity_score = high_count * 2 + medium_count
        
        # JIRA adjustments
        if jira_data:
            issue_type = jira_data.get('issue_type', '').lower()
            priority = jira_data.get('priority', 'medium').lower()
            
            if issue_type in ['epic', 'story']:
                complexity_score += 2
            elif issue_type in ['task', 'improvement']:
                complexity_score += 1
            
            if priority in ['critical', 'highest']:
                complexity_score += 1.5
            elif priority in ['high', 'major']:
                complexity_score += 1
        
        # Special handling for React Native upgrades
        if any(keyword in description_lower for keyword in ['react native', 'upgrade', 'migration']):
            if any(keyword in description_lower for keyword in ['objective-c', 'swift', 'native']):
                # React Native + Native migration = Very High complexity
                complexity = 'High'
                base_hours = 300
            else:
                # React Native upgrade only = High complexity
                complexity = 'High'
                base_hours = 200
        # Standard complexity determination
        elif complexity_score >= 4:
            complexity = 'High'
            base_hours = 160
        elif complexity_score >= 2:
            complexity = 'Medium'
            base_hours = 80
        else:
            complexity = 'Low'
            base_hours = 40
        
        # Phase distribution
        phases = {
            'requirements': round(base_hours * 0.15, 1),
            'design': round(base_hours * 0.20, 1),
            'development': round(base_hours * 0.45, 1),
            'testing': round(base_hours * 0.15, 1),
            'deployment': round(base_hours * 0.05, 1)
        }
        
        return {
            'total_hours': base_hours,
            'complexity': complexity,
            'confidence': 60,
            'reasoning': 'Rule-based fallback estimation',
            'phases': phases,
            'estimation_method': 'rule_based_fallback'
        }