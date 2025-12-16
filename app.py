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
from ai_modules.ai_estimator import AIEstimator

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
        
        # Extract comments
        comments = []
        if 'comment' in data['fields'] and data['fields']['comment']['comments']:
            for comment in data['fields']['comment']['comments']:
                comments.append({
                    'author': comment['author']['displayName'],
                    'body': comment['body'],
                    'created': comment['created']
                })
        
        # Extract labels
        labels = data['fields'].get('labels', [])
        
        # Extract linked issues
        linked_issues = []
        if 'issuelinks' in data['fields']:
            for link in data['fields']['issuelinks']:
                if 'outwardIssue' in link:
                    linked_issues.append({
                        'key': link['outwardIssue']['key'],
                        'summary': link['outwardIssue']['fields']['summary'],
                        'type': link['type']['outward']
                    })
                if 'inwardIssue' in link:
                    linked_issues.append({
                        'key': link['inwardIssue']['key'],
                        'summary': link['inwardIssue']['fields']['summary'],
                        'type': link['type']['inward']
                    })
        
        # Extract fix versions
        fix_versions = []
        if 'fixVersions' in data['fields']:
            for version in data['fields']['fixVersions']:
                fix_versions.append({
                    'name': version['name'],
                    'released': version.get('released', False)
                })
        
        return {
            'key': data['key'],
            'summary': data['fields']['summary'],
            'description': data['fields'].get('description', ''),
            'issue_type': data['fields']['issuetype']['name'],
            'priority': data['fields'].get('priority', {}).get('name', 'Medium'),
            'status': data['fields']['status']['name'],
            'comments': comments,
            'labels': labels,
            'linked_issues': linked_issues,
            'fix_versions': fix_versions
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
            'development': 0.48,
            'testing': 0.15,
            'deployment': 0.02
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
        
        # Original keyword analysis
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
        
        complexity_score += high_count * 2 + medium_count
        
        # JIRA-based complexity factors
        if jira_data:
            issue_type = jira_data.get('issue_type', '').lower()
            priority = jira_data.get('priority', 'medium').lower()
            
            # Issue type complexity
            if issue_type in ['epic', 'story']:
                complexity_score += 2
            elif issue_type in ['task', 'improvement']:
                complexity_score += 1
            elif issue_type == 'bug':
                complexity_score += 0.5
            
            # Priority impact
            if priority in ['critical', 'highest']:
                complexity_score += 1.5
            elif priority in ['high', 'major']:
                complexity_score += 1
        
        # Description length factor
        if len(description.split()) > 50:
            complexity_score += 1
        
        # Determine final complexity
        if complexity_score >= 4:
            return 'High'
        elif complexity_score >= 2:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_base_hours(self, complexity, jira_data=None):
        """Get base hours based on complexity and JIRA factors"""
        complexity_hours = {
            'Low': 40,
            'Medium': 80,
            'High': 160
        }
        
        base_hours = complexity_hours.get(complexity, 80)
        
        # Adjust based on JIRA factors
        if jira_data:
            issue_type = jira_data.get('issue_type', '').lower()
            priority = jira_data.get('priority', 'medium').lower()
            
            # Issue type multiplier
            if issue_type == 'epic':
                base_hours *= 1.5
            elif issue_type == 'bug':
                base_hours *= 0.7
            
            # Priority multiplier
            if priority in ['critical', 'highest']:
                base_hours *= 1.2
            elif priority in ['low', 'lowest']:
                base_hours *= 0.8
        
        return round(base_hours)

estimator = ProjectEstimator()

# Initialize AI components
design_generator = SolutionDesigner(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)
code_generator = AICodeGenerator(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)
codebase_analyzer = CodebaseAnalyzer()
approval_workflow = DesignApprovalWorkflow()
ai_estimator = AIEstimator(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

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
        
        # Check if AI estimation is requested
        use_ai = data.get('use_ai', False)
        selected_phases = data.get('selected_phases', {
            'requirements': True,
            'design': True,
            'development': True,
            'testing': True,
            'deployment': True
        })
        
        phase_percentages = data.get('phase_percentages', {
            'requirements': 15,
            'design': 20,
            'development': 48,
            'testing': 15,
            'deployment': 2
        })
        
        custom_phases = data.get('custom_phases', {})
        
        print(f"DEBUG - AI Estimation requested: {use_ai}")
        print(f"DEBUG - Azure API key configured: {bool(os.getenv('AZURE_OPENAI_API_KEY'))}")
        
        if use_ai and os.getenv('AZURE_OPENAI_API_KEY'):
            print("DEBUG - Using AI estimation with FAB model")
            # Use AI estimation
            ai_result = ai_estimator.estimate_with_ai(description, jira_data)
            
            # Check if status filtering should override custom percentages
            status = jira_data.get('status', '').lower() if jira_data else ''
            status_override = status in ['qa', 'sit', 'testing', 'ready for testing', 'in testing', 'uat', 'user acceptance testing', 'ready for deployment', 'staging', 'done', 'closed', 'resolved', 'deployed', 'production', 'in progress', 'development', 'coding', 'in development']
            
            if status_override:
                print(f"DEBUG - Status '{status}' detected, applying status-based filtering instead of custom percentages")
                # Apply status filtering to AI result first
                ai_result = ai_estimator._apply_status_based_filtering(ai_result, jira_data)
                filtered_phases = ai_result.get('phases', {})
                total_filtered_hours = ai_result.get('total_hours', 0)
            else:
                # Apply custom percentages and filter phases
                base_total = ai_result.get('total_hours', 80)
                print(f"DEBUG - AI base total hours: {base_total}")
                print(f"DEBUG - Phase percentages: {phase_percentages}")
                
                filtered_phases = {}
                total_filtered_hours = 0
                
                # Process standard phases
                for phase in ['requirements', 'design', 'development', 'testing', 'deployment']:
                    if selected_phases.get(phase, True):
                        custom_hours = round(base_total * (phase_percentages.get(phase, 0) / 100), 1)
                        print(f"DEBUG - {phase}: {phase_percentages.get(phase, 0)}% of {base_total} = {custom_hours} hours")
                        filtered_phases[phase] = custom_hours
                        total_filtered_hours += custom_hours
                
                # Process custom phases
                for phase_key in custom_phases.keys():
                    if selected_phases.get(phase_key, True):
                        custom_hours = round(base_total * (phase_percentages.get(phase_key, 0) / 100), 1)
                        print(f"DEBUG - {phase_key}: {phase_percentages.get(phase_key, 0)}% of {base_total} = {custom_hours} hours")
                        filtered_phases[phase_key] = custom_hours
                        total_filtered_hours += custom_hours
                
                print(f"DEBUG - Total filtered hours: {total_filtered_hours}")
            
            # Format result to match existing structure
            estimate_result = {
                'jira_number': jira_number,
                'description': description,
                'complexity': ai_result.get('complexity', 'Medium'),
                'total_hours': total_filtered_hours,
                'phases': filtered_phases,
                'estimated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'estimation_method': ai_result.get('estimation_method', 'ai_powered'),
                'ai_confidence': ai_result.get('confidence', 75),
                'ai_reasoning': ai_result.get('reasoning', ''),
                'risk_factors': ai_result.get('risk_factors', []),
                'custom_phase_names': custom_phases
            }
            
            if jira_data:
                estimate_result['jira_details'] = {
                    'issue_type': jira_data.get('issue_type'),
                    'priority': jira_data.get('priority', 'Medium'),
                    'status': jira_data.get('status')
                }
        else:
            print("DEBUG - Using rule-based estimation (no AI)")
            # Use rule-based estimation
            estimate_result = estimator.estimate_project(description, jira_number, jira_data)
            
            # Apply custom percentages and filter phases
            base_total = estimate_result['total_hours']
            filtered_phases = {}
            total_filtered_hours = 0
            
            # Process standard phases
            for phase in ['requirements', 'design', 'development', 'testing', 'deployment']:
                if selected_phases.get(phase, True):
                    custom_hours = round(base_total * (phase_percentages.get(phase, 0) / 100), 1)
                    filtered_phases[phase] = custom_hours
                    total_filtered_hours += custom_hours
            
            # Process custom phases
            for phase_key in custom_phases.keys():
                if selected_phases.get(phase_key, True):
                    custom_hours = round(base_total * (phase_percentages.get(phase_key, 0) / 100), 1)
                    filtered_phases[phase_key] = custom_hours
                    total_filtered_hours += custom_hours
            
            estimate_result['phases'] = filtered_phases
            estimate_result['total_hours'] = total_filtered_hours
            estimate_result['estimation_method'] = 'rule_based'
            estimate_result['custom_phase_names'] = custom_phases
        
        return jsonify(estimate_result)
    except Exception as e:
        print(f"Error in estimate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    return jsonify([])

@app.route('/generate-design', methods=['POST'])
def generate_design():
    try:
        data = request.get_json()
        ticket_key = data.get('ticket_key')
        repo_path = data.get('repo_path', '')
        
        if not ticket_key:
            return jsonify({'error': 'Ticket key is required'}), 400
        
        jira_data = jira_client.get_ticket_details(ticket_key)
        
        codebase_context = {}
        if repo_path and os.path.exists(repo_path):
            codebase_context = codebase_analyzer.analyze_codebase(repo_path)
        
        design = design_generator.generate_solution_design(jira_data, codebase_context)
        
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
        
        approval_workflow.add_approval_comment(approval_id, approver, comment, approved)
        
        if approved:
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
        
        approved_design_data = approval_workflow.get_approved_design(approval_id)
        if not approved_design_data:
            return jsonify({'error': 'Design not found or not approved'}), 400
        
        design = approved_design_data['design']
        ticket_key = approved_design_data['ticket_key']
        
        jira_data = jira_client.get_ticket_details(ticket_key)
        
        if repo_path and os.path.exists(repo_path):
            generated_code = code_generator.generate_code_from_design(design, repo_path, jira_data)
        else:
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

@app.route('/test-ai', methods=['GET'])
def test_ai_connection():
    """Test Azure OpenAI FAB API connection"""
    try:
        # Test simple AI call
        test_result = ai_estimator.estimate_with_ai("Create a simple login form with username and password")
        
        return jsonify({
            'status': 'success',
            'ai_working': True,
            'estimation_method': test_result.get('estimation_method'),
            'test_hours': test_result.get('total_hours'),
            'message': 'AI connection working'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'ai_working': False,
            'error': str(e),
            'message': 'AI connection failed'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)