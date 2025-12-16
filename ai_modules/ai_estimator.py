from openai import AzureOpenAI
import json
import os
import hashlib
from typing import Dict, Any

class AIEstimator:
    def __init__(self, api_key: str = None, azure_endpoint: str = None):
        self.api_key = api_key
        self.azure_endpoint = azure_endpoint
        self.client = None
        self.cache = {}  # Cache for consistent results
        
        if api_key and azure_endpoint:
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=azure_endpoint
            )
    
    def estimate_with_ai(self, description: str, jira_data: Dict = None) -> Dict:
        """Use AI to estimate project complexity and hours"""
        
        # Create cache key from input
        cache_key = self._create_cache_key(description, jira_data)
        
        # Check cache first
        if cache_key in self.cache:
            print("DEBUG - Returning cached result for consistent estimation")
            return self.cache[cache_key]
        
        print(f"DEBUG - AI Estimator called with API key: {bool(self.api_key)}")
        print(f"DEBUG - Azure endpoint: {self.azure_endpoint}")
        
        if not self.api_key:
            print("DEBUG - No API key, using fallback estimation")
            # Fallback to rule-based estimation
            result = self._fallback_estimation(description, jira_data)
            self.cache[cache_key] = result
            return result
        
        try:
            print("DEBUG - Calling FAB API for estimation...")
            # Prepare context for AI
            context = self._build_estimation_context(description, jira_data)
            
            # Get AI estimation
            ai_response = self._get_ai_estimation(context)
            print(f"DEBUG - AI Response received: {ai_response[:200]}...")
            
            # Parse and validate AI response
            estimation = self._parse_ai_response(ai_response, jira_data)
            
            # Cache the result
            self.cache[cache_key] = estimation
            
            return estimation
            
        except Exception as e:
            print(f"DEBUG - AI estimation failed: {str(e)}")
            print(f"DEBUG - Falling back to rule-based estimation")
            # Fallback to rule-based estimation
            result = self._fallback_estimation(description, jira_data)
            self.cache[cache_key] = result
            return result
    
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
            
            # Add labels if available
            if jira_data.get('labels'):
                context += f"\n            - Labels: {', '.join(jira_data['labels'])}"
            
            # Add fix versions if available
            if jira_data.get('fix_versions'):
                versions = [v['name'] for v in jira_data['fix_versions']]
                context += f"\n            - Fix Versions: {', '.join(versions)}"
            
            # Add linked issues if available
            if jira_data.get('linked_issues'):
                linked_info = [f"{link['key']} ({link['type']})" for link in jira_data['linked_issues']]
                context += f"\n            - Linked Issues: {', '.join(linked_info)}"
            
            # Add recent comments if available
            if jira_data.get('comments'):
                recent_comments = jira_data['comments'][-2:]  # Last 2 comments
                context += "\n            - Recent Comments:"
                for comment in recent_comments:
                    comment_text = comment['body'][:150] + "..." if len(comment['body']) > 150 else comment['body']
                    context += f"\n              * {comment['author']}: {comment_text}"
        
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
        
        **SPECIAL CASE - BlackDuck Security Tickets:**
        - If description mentions "BlackDuck", "security vulnerability", "CVE", "dependency update", or "version upgrade" for security:
        - MAXIMUM 32 hours total
        - NO design phase (0 hours)
        - Minimal testing (security scan validation only)
        - Focus on: Requirements (4h), Development (24h), Testing (3h), Deployment (1h)
        
        **Keywords that indicate HIGH complexity (200+ hours):**
        - "React Native upgrade" + version numbers
        - "Objective-C to Swift"
        - "native dependencies"
        - "third party dependencies"
        - "breaking changes"
        - "migration"
        
        **CONFIDENCE SCORING GUIDELINES:**
        - 90-95%: Simple, well-defined tasks with clear requirements
        - 80-89%: Moderate complexity with some unknowns
        - 70-79%: Complex tasks with multiple dependencies
        - 60-69%: High complexity with significant unknowns
        - 50-59%: Very complex with many risk factors
        
        **IMPORTANT: Respond ONLY with valid JSON, no additional text:**
        {
            "total_hours": <number>,
            "complexity": "<Low|Medium|High>",
            "confidence": <number between 50-95 based on task clarity>,
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
    
    def _create_cache_key(self, description: str, jira_data: Dict = None) -> str:
        """Create a unique cache key from input parameters"""
        
        # Combine description and relevant JIRA data
        cache_input = description.lower().strip()
        
        if jira_data:
            jira_key_parts = [
                jira_data.get('issue_type', ''),
                jira_data.get('priority', ''),
                jira_data.get('summary', ''),
                jira_data.get('description', '')
            ]
            cache_input += '|' + '|'.join(jira_key_parts)
        
        # Create hash for consistent key
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _calculate_reliable_confidence(self, estimation: Dict, jira_data: Dict = None) -> int:
        """Calculate confidence based on actual project factors, not AI guesswork"""
        
        base_confidence = 85  # Start with high confidence
        
        # Factor 1: Complexity reduces confidence
        complexity = estimation.get('complexity', 'Medium')
        if complexity == 'High':
            base_confidence -= 20
        elif complexity == 'Medium':
            base_confidence -= 10
        # Low complexity: no reduction
        
        # Factor 2: Very high or very low hours indicate uncertainty
        total_hours = estimation.get('total_hours', 80)
        if total_hours > 300:  # Very large projects
            base_confidence -= 15
        elif total_hours > 200:
            base_confidence -= 10
        elif total_hours < 20:  # Very small projects might be underestimated
            base_confidence -= 5
        
        # Factor 3: JIRA data availability increases confidence
        if jira_data:
            base_confidence += 5  # Having structured requirements helps
            
            # Well-defined issue types increase confidence
            issue_type = jira_data.get('issue_type', '').lower()
            if issue_type in ['story', 'task']:
                base_confidence += 5
            elif issue_type in ['epic']:  # Epics are usually less defined
                base_confidence -= 5
        else:
            base_confidence -= 10  # No structured requirements
        
        # Factor 4: Estimation method affects confidence
        method = estimation.get('estimation_method', '')
        if method == 'ai_powered':
            base_confidence += 5  # AI analysis adds value
        elif method == 'rule_based_fallback':
            base_confidence -= 10  # Fallback is less reliable
        
        # Factor 5: Keywords indicating uncertainty
        reasoning = estimation.get('reasoning', '').lower()
        uncertainty_keywords = ['migration', 'upgrade', 'complex', 'unknown', 'unclear']
        uncertainty_count = sum(1 for keyword in uncertainty_keywords if keyword in reasoning)
        base_confidence -= uncertainty_count * 5
        
        # Ensure confidence stays within reasonable bounds
        return max(50, min(95, base_confidence))
    
    def _apply_blackduck_capping(self, estimation: Dict, jira_data: Dict = None) -> Dict:
        """Apply BlackDuck ticket capping rules"""
        
        # Check if this is a BlackDuck security ticket
        description = estimation.get('reasoning', '').lower()
        blackduck_keywords = ['blackduck', 'security vulnerability', 'cve', 'dependency update', 'version upgrade']
        
        # Also check JIRA data if available
        jira_text = ''
        if jira_data:
            jira_text = f"{jira_data.get('summary', '')} {jira_data.get('description', '')}".lower()
        
        is_blackduck = any(keyword in description for keyword in blackduck_keywords) or \
                      any(keyword in jira_text for keyword in blackduck_keywords)
        
        if is_blackduck:
            print("DEBUG - BlackDuck ticket detected, applying 32-hour cap")
            
            # Cap at 32 hours with specific phase distribution
            estimation['total_hours'] = 32
            estimation['complexity'] = 'Low'
            estimation['phases'] = {
                'requirements': 4,
                'design': 0,  # No design needed for security updates
                'development': 24,
                'testing': 3,
                'deployment': 1
            }
            estimation['reasoning'] = f"BlackDuck security ticket - capped at 32 hours. {estimation.get('reasoning', '')}"
        
        # Apply status-based phase filtering
        estimation = self._apply_status_based_filtering(estimation, jira_data)
        
        return estimation
    
    def _apply_status_based_filtering(self, estimation: Dict, jira_data: Dict = None) -> Dict:
        """Filter phases based on JIRA ticket status"""
        
        if not jira_data or 'status' not in jira_data:
            return estimation
        
        status = jira_data.get('status', '').lower()
        phases = estimation.get('phases', {})
        
        # Define status-to-phase mapping
        if status in ['qa', 'sit', 'testing', 'ready for testing', 'in testing']:
            # Only testing and deployment remain
            phases['requirements'] = 0
            phases['design'] = 0
            phases['development'] = 0
            estimation['reasoning'] += f" Ticket in {status} - only testing and deployment phases remain."
            
        elif status in ['uat', 'user acceptance testing', 'ready for deployment', 'staging']:
            # Only deployment remains
            phases['requirements'] = 0
            phases['design'] = 0
            phases['development'] = 0
            phases['testing'] = 0
            estimation['reasoning'] += f" Ticket in {status} - only deployment phase remains."
            
        elif status in ['done', 'closed', 'resolved', 'deployed', 'production']:
            # All phases complete
            phases['requirements'] = 0
            phases['design'] = 0
            phases['development'] = 0
            phases['testing'] = 0
            phases['deployment'] = 0
            estimation['reasoning'] += f" Ticket {status} - no remaining work."
            
        elif status in ['in progress', 'development', 'coding', 'in development']:
            # Requirements and design likely complete
            phases['requirements'] = 0
            phases['design'] = 0
            estimation['reasoning'] += f" Ticket in {status} - requirements and design phases complete."
        
        # Recalculate total hours
        estimation['total_hours'] = sum(phases.values())
        estimation['phases'] = phases
        
        return estimation
    
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
            max_completion_tokens=1000,
            seed=12345  # Fixed seed for consistent results
        )
        
        return response.choices[0].message.content
    
    def _parse_ai_response(self, ai_response: str, jira_data: Dict = None) -> Dict:
        """Parse AI response into structured estimation"""
        
        print(f"DEBUG - Full AI Response: {ai_response}")
        
        try:
            # Try to extract JSON from response
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = ai_response[start:end]
                print(f"DEBUG - Extracted JSON: {json_str}")
                estimation = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['total_hours', 'complexity', 'phases']
                if all(field in estimation for field in required_fields):
                    # Apply BlackDuck capping if needed
                    estimation = self._apply_blackduck_capping(estimation, jira_data)
                    
                    # Calculate reliable confidence based on actual factors
                    reliable_confidence = self._calculate_reliable_confidence(estimation, jira_data)
                    
                    # Add metadata
                    estimation['estimation_method'] = 'ai_powered'
                    estimation['ai_confidence'] = reliable_confidence
                    estimation['ai_original_confidence'] = estimation.get('confidence', 'N/A')  # Keep AI's original for reference
                    print(f"DEBUG - AI JSON parsed successfully, reliable confidence: {reliable_confidence}%")
                    
                    return estimation
                else:
                    print(f"DEBUG - Missing required fields: {[f for f in required_fields if f not in estimation]}")
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"DEBUG - Failed to parse AI JSON: {e}")
        
        # If parsing fails, extract key information manually
        print("DEBUG - Falling back to manual extraction")
        return self._extract_estimation_manually(ai_response, jira_data)
    
    def _extract_estimation_manually(self, ai_response: str, jira_data: Dict = None) -> Dict:
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
            'development': round(total_hours * 0.48, 1),
            'testing': round(total_hours * 0.15, 1),
            'deployment': round(total_hours * 0.02, 1)
        }
        
        result = {
            'total_hours': total_hours,
            'complexity': complexity,
            'reasoning': 'Extracted from AI response text',
            'phases': phases,
            'estimation_method': 'ai_extracted',
            'ai_response': ai_response[:500]  # First 500 chars for debugging
        }
        
        # Apply BlackDuck capping if needed
        result = self._apply_blackduck_capping(result, jira_data)
        
        # Calculate reliable confidence
        result['confidence'] = self._calculate_reliable_confidence(result, jira_data)
        
        return result
    
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
            'development': round(base_hours * 0.48, 1),
            'testing': round(base_hours * 0.15, 1),
            'deployment': round(base_hours * 0.02, 1)
        }
        
        result = {
            'total_hours': base_hours,
            'complexity': complexity,
            'reasoning': 'Rule-based fallback estimation',
            'phases': phases,
            'estimation_method': 'rule_based_fallback'
        }
        
        # Apply BlackDuck capping if needed
        result = self._apply_blackduck_capping(result, jira_data)
        
        # Apply status-based phase filtering
        result = self._apply_status_based_filtering(result, jira_data)
        
        # Calculate reliable confidence
        result['confidence'] = self._calculate_reliable_confidence(result, jira_data)
        
        return result