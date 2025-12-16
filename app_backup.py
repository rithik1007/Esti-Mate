from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
import json
import requests
from requests.auth import HTTPBasicAuth
import base64
from dotenv import load_dotenv

# Import AI modules
from ai_modules.design_generator.solution_designer import SolutionDesigner, DesignApprovalWorkflow
from ai_modules.code_generator.code_generator import AICodeGenerator
from ai_modules.repo_analyzer.codebase_analyzer import CodebaseAnalyzer

load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'

class JiraClient:
    def __init__(self):
        self.base_url = None
        self.token = None
        self.email = None
    
    def configure(self, base_url, email, token):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.token = token
    
    def get_ticket_details(self, ticket_key):
        if not all([self.base_url, self.email, self.token]):
            raise Exception("JIRA configuration missing. Please configure JIRA settings first.")
        
        url = f"{self.base_url}/rest/api/2/issue/{ticket_key}"
        auth = HTTPBasicAuth(self.email, self.token)
        
        print(f"Fetching JIRA ticket from: {url}")
        print(f"Using email: {self.email}")
        
        try:
            response = requests.get(url, auth=auth, timeout=10)
        except requests.exceptions.Timeout:
            raise Exception("JIRA request timed out. Please check your JIRA server URL and try again.")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to JIRA server. Please check your JIRA base URL and internet connection.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while connecting to JIRA: {str(e)}")
        
        if response.status_code == 404:
            raise Exception(f"Ticket '{ticket_key}' not found. Please verify the ticket number exists and you have permission to view it.")
        elif response.status_code == 401:
            raise Exception("Authentication failed. Please check your JIRA email and API token are correct.")
        elif response.status_code == 403:
            raise Exception(f"Access denied to ticket '{ticket_key}'. You don't have permission to view this ticket.")
        elif response.status_code == 400:
            raise Exception(f"Invalid ticket format '{ticket_key}'. Please use format like 'PROJ-123'.")
        elif response.status_code != 200:
            raise Exception(f"JIRA server error ({response.status_code}). Please try again later or contact your JIRA administrator.")
        
        data = response.json()
        return {
            'key': data['key'],
            'summary': data['fields']['summary'],
            'description': data['fields'].get('description', ''),
            'issue_type': data['fields']['issuetype']['name'],
            'priority': data['fields'].get('priority', {}).get('name', 'Medium'),
            'status': data['fields']['status']['name']
        }

jira_client = JiraClient()
# Auto-configure from environment variables
if all([os.getenv('JIRA_BASE_URL'), os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN')]):
    jira_client.configure(
        os.getenv('JIRA_BASE_URL'),
        os.getenv('JIRA_EMAIL'),
        os.getenv('JIRA_API_TOKEN')
    )

class ProjectEstimator:
    def __init__(self):
        self.phase_weights = {
            'requirements': 0.15,
            'design': 0.20,
            'development': 0.45,
            'testing': 0.15,
            'deployment': 0.05
        }
    
    def estimate_project(self, description, jira_number=None, jira_data=None):
        """Estimate project phases based on description and JIRA data"""
        
        # Analyze complexity with JIRA data
        complexity = self._analyze_complexity(description, jira_data)
        base_hours = self._get_base_hours(complexity, jira_data)
        
        # Calculate phase estimates
        estimates = {}
        for phase, weight in self.phase_weights.items():
            estimates[phase] = round(base_hours * weight, 1)
        
        result = {
            'jira_number': jira_number,
            'description': description,
            'complexity': complexity,
            'total_hours': base_hours,
            'phases': estimates,
            'estimated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if jira_data:
            result['jira_details'] = {
                'issue_type': jira_data.get('issue_type'),
                'priority': jira_data.get('priority', 'Medium'),
                'status': jira_data.get('status')
            }
        
        return result
    
    def _analyze_complexity(self, description, jira_data=None):
        """Analyze project complexity based on keywords and JIRA data"""
        description_lower = description.lower()
        complexity_score = 0
        
        # Simplified keyword analysis - back to original smaller lists
        high_complexity_keywords = [
            'integration', 'api', 'database', 'migration', 'security',
            'authentication', 'microservice', 'complex', 'multiple systems'
        ]
        
        medium_complexity_keywords = [
            'crud', 'form', 'validation', 'report', 'dashboard',
            'ui', 'frontend', 'backend'
        ]
        
        high_count = sum(1 for keyword in high_complexity_keywords if keyword in description_lower)
        medium_count = sum(1 for keyword in medium_complexity_keywords if keyword in description_lower)
        
        # Debug logging
        print(f"DEBUG - Description: {description[:100]}...")
        print(f"DEBUG - High keywords found: {high_count}")
        print(f"DEBUG - Medium keywords found: {medium_count}")
        
        complexity_score += high_count * 2 + medium_count
        print(f"DEBUG - Keyword score: {complexity_score}")
        
        # JIRA complexity additions
        jira_score_addition = 0
        if jira_data:
            issue_type = jira_data.get('issue_type', '').lower()
            priority = jira_data.get('priority', 'medium').lower()
            
            # Issue type complexity
            if issue_type in ['epic', 'story']:
                jira_score_addition += 2
            elif issue_type in ['task', 'improvement']:
                jira_score_addition += 1
            elif issue_type == 'bug':
                jira_score_addition += 0.5
            
            # Priority impact
            if priority in ['critical', 'highest']:
                jira_score_addition += 1.5
            elif priority in ['high', 'major']:
                jira_score_addition += 1
            
            print(f"DEBUG - JIRA additions: {jira_score_addition} (type: {issue_type}, priority: {priority})")
        
        complexity_score += jira_score_addition
        
        # Description length factor
        length_addition = 0
        if len(description.split()) > 50:
            length_addition = 1
            complexity_score += 1
        
        print(f"DEBUG - Final complexity score: {complexity_score}")
        
        # Determine final complexity
        if complexity_score >= 4:
            final_complexity = 'High'
        elif complexity_score >= 2:
            final_complexity = 'Medium'
        else:
            final_complexity = 'Low'
        
        print(f"DEBUG - Final complexity: {final_complexity} (score: {complexity_score})")
        return final_complexityor']:
                jira_score_addition += 1
            
            print(f"DEBUG - JIRA additions: {jira_score_addition} (type: {issue_type}, priority: {priority})")
        
        complexity_score += jira_score_addition
        
        # Description length factor
        length_addition = 0
        if len(description.split()) > 50:
            length_addition = 1
            complexity_score += 1
        
        print(f"DEBUG - Final complexity score: {complexity_score} (keywords: {high_count * 2 + medium_count}, jira: {jira_score_addition}, length: {length_addition})")
        
        # Determine final complexity
        if complexity_score >= 4:
            final_complexity = 'High'
        elif complexity_score >= 2:
            final_complexity = 'Medium'
        else:
            final_complexity = 'Low'
        
        print(f"DEBUG - Final complexity: {final_complexity} (score: {complexity_score})")
        return final_complexity   elif issue_type == 'bug':
                jira_score_addition += 0.5
            
            # Priority impact
            if priority in ['critical', 'highest']:
                jira_score_addition += 1.5
            elif priority in ['high', 'major']:
                jira_score_addition += 1
            
            print(f"DEBUG - JIRA additions: {jira_score_addition} (type: {issue_type}, priority: {priority})")
        
        complexity_score += jira_score_addition
        
        # Description length factor
        length_addition = 0
        if len(description.split()) > 50:
            length_addition = 1
            complexity_score += 1
        
        print(f"DEBUG - Final complexity score: {complexity_score} (keywords: {high_count * 2 + medium_count}, jira: {jira_score_addition}, length: {length_addition})")
            complexity_score += 1
        
        # Determine final complexity
        if complexity_score >= 4:
            final_complexity = 'High'
        elif complexity_score >= 2:
            final_complexity = 'Medium'
        else:
            final_complexity = 'Low'
        
        print(f"DEBUG - Final complexity: {final_complexity} (score: {complexity_score})")
        return final_complexity
    
    def _get_base_hours(self, complexity, jira_data=None):
        """Get base hours based on complexity and JIRA factors"""
        complexity_hours = {
            'Low': 40,
            'Medium': 80,
            'High': 160
        }
        
        base_hours = complexity_hours.get(complexity, 80)
        print(f"DEBUG - Base hours for {complexity}: {base_hours}")
        
        # Adjust based on JIRA factors
        multiplier = 1.0
        if jira_data:
            issue_type = jira_data.get('issue_type', '').lower()
            priority = jira_data.get('priority', 'medium').lower()
            
            # Issue type multiplier
            if issue_type == 'epic':
                multiplier *= 1.5
                print(f"DEBUG - Epic multiplier: 1.5")
            elif issue_type == 'bug':
                multiplier *= 0.7
                print(f"DEBUG - Bug multiplier: 0.7")
            
            # Priority multiplier
            if priority in ['critical', 'highest']:
                multiplier *= 1.2
                print(f"DEBUG - Critical/Highest priority multiplier: 1.2")
            elif priority in ['low', 'lowest']:
                multiplier *= 0.8
                print(f"DEBUG - Low priority multiplier: 0.8")
        
        final_hours = round(base_hours * multiplier)
        print(f"DEBUG - Final hours: {base_hours} * {multiplier} = {final_hours}")
        return final_hours

    def estimate_with_ai_context(self, description, jira_data=None, codebase_context=None):
        """Enhanced estimation using AI and codebase context"""
        
        # Get base estimate
        base_estimate = self.estimate_project(description, jira_data=jira_data)
        
        # Adjust based on codebase complexity
        if codebase_context:
            tech_stack = codebase_context.get('tech_stack', {})
            complexity_factors = codebase_context.get('code_patterns', {})
            
            # Adjust for technology complexity
            if 'microservices' in str(tech_stack).lower():
                base_estimate['total_hours'] *= 1.3
            elif 'monolith' in str(tech_stack).lower():
                base_estimate['total_hours'] *= 0.9
            
            # Adjust for codebase maturity
            if len(complexity_factors.get('class_patterns', [])) > 10:
                base_estimate['total_hours'] *= 0.8  # Mature codebase
            
            # Recalculate phases
            for phase, weight in self.phase_weights.items():
                base_estimate['phases'][phase] = round(base_estimate['total_hours'] * weight, 1)
        
        return base_estimate

estimator = ProjectEstimator()

# Initialize AI components
design_generator = SolutionDesigner(api_key=os.getenv('OPENAI_API_KEY'))
code_generator = AICodeGenerator(api_key=os.getenv('OPENAI_API_KEY'))
codebase_analyzer = CodebaseAnalyzer()
approval_workflow = DesignApprovalWorkflow()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ai-workflow')
def ai_workflow():
    return render_template('ai_workflow.html')

@app.route('/configure-jira', methods=['POST'])
def configure_jira():
    try:
        data = request.get_json()
        base_url = data.get('base_url')
        email = data.get('email')
        token = data.get('token')
        
        if not all([base_url, email, token]):
            return jsonify({'error': 'All JIRA fields are required'}), 400
        
        jira_client.configure(base_url, email, token)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/estimate', methods=['POST'])
def estimate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
            
        description = data.get('description', '')
        jira_number = data.get('jira_number', '')
        use_jira = data.get('use_jira', False)
        
        jira_data = None
        if use_jira and jira_number:
            try:
                jira_data = jira_client.get_ticket_details(jira_number)
                description = f"{jira_data['summary']}. {jira_data['description']}"
                jira_number = jira_data['key']
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'error_type': 'jira_error'
                }), 400
        
        if not description:
            return jsonify({'error': 'Description is required'}), 400
        
        estimate_result = estimator.estimate_project(description, jira_number, jira_data)
        return jsonify(estimate_result)
    except Exception as e:
        print(f"Error in estimate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    # In a real app, this would fetch from a database
    return jsonify([])

@app.route('/generate-design', methods=['POST'])
def generate_design():
    try:
        data = request.get_json()
        ticket_key = data.get('ticket_key')
        repo_path = data.get('repo_path', '')
        
        if not ticket_key:
            return jsonify({'error': 'Ticket key is required'}), 400
        
        # Get ticket details
        jira_data = jira_client.get_ticket_details(ticket_key)
        
        # Analyze codebase if path provided
        codebase_context = {}
        if repo_path and os.path.exists(repo_path):
            codebase_context = codebase_analyzer.analyze_codebase(repo_path)
        
        # Generate solution design
        design = design_generator.generate_solution_design(jira_data, codebase_context)
        
        # Submit for approval
        approvers = data.get('approvers', ['tech_lead', 'architect'])
        approval_id = approval_workflow.submit_for_approval(ticket_key, design, approvers)
        
        return jsonify({
            'design': design,
            'approval_id': approval_id,
            'status': 'pending_approval',
            'ticket_key': ticket_key
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/approve-design', methods=['POST'])
def approve_design():
    try:
        data = request.get_json()
        approval_id = data.get('approval_id')
        approver = data.get('approver')
        approved = data.get('approved', False)
        comment = data.get('comment', '')
        
        if not all([approval_id, approver]):
            return jsonify({'error': 'Approval ID and approver are required'}), 400
        
        # Add approval comment
        approval_workflow.add_approval_comment(approval_id, approver, comment, approved)
        
        if approved:
            # Approve the design
            success = approval_workflow.approve_design(approval_id, approver)
            if success:
                return jsonify({'status': 'approved', 'message': 'Design approved successfully'})
            else:
                return jsonify({'error': 'Failed to approve design'}), 400
        else:
            return jsonify({'status': 'feedback_provided', 'message': 'Feedback added to design'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-code', methods=['POST'])
def generate_code():
    try:
        data = request.get_json()
        approval_id = data.get('approval_id')
        repo_path = data.get('repo_path', '')
        
        if not approval_id:
            return jsonify({'error': 'Approval ID is required'}), 400
        
        # Get approved design
        approved_design_data = approval_workflow.get_approved_design(approval_id)
        if not approved_design_data:
            return jsonify({'error': 'Design not found or not approved'}), 400
        
        design = approved_design_data['design']
        ticket_key = approved_design_data['ticket_key']
        
        # Get ticket details
        jira_data = jira_client.get_ticket_details(ticket_key)
        
        # Generate code
        if repo_path and os.path.exists(repo_path):
            generated_code = code_generator.generate_code_from_design(design, repo_path, jira_data)
        else:
            # Generate without codebase context
            generated_code = code_generator.generate_code_from_design(design, '', jira_data)
        
        return jsonify({
            'generated_code': generated_code,
            'ticket_key': ticket_key,
            'design_id': approval_id,
            'status': 'code_generated'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-codebase', methods=['POST'])
def analyze_codebase():
    try:
        data = request.get_json()
        repo_path = data.get('repo_path')
        
        if not repo_path:
            return jsonify({'error': 'Repository path is required'}), 400
        
        if not os.path.exists(repo_path):
            return jsonify({'error': 'Repository path does not exist'}), 400
        
        # Analyze codebase
        analysis = codebase_analyzer.analyze_codebase(repo_path)
        
        return jsonify({
            'analysis': analysis,
            'repo_path': repo_path,
            'status': 'analysis_complete'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/pending-designs')
def get_pending_designs():
    try:
        pending = approval_workflow.get_pending_designs()
        return jsonify({'pending_designs': pending})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)