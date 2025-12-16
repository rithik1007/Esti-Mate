# Esti-Mate: AI-Powered Project Estimator

An intelligent web application that provides accurate project time estimates using AI and JIRA integration. Perfect for software development teams who need realistic project planning.

## 🚀 Features

### Core Estimation
- **AI-Powered Analysis**: Uses Azure OpenAI to analyze project complexity and provide intelligent estimates
- **JIRA Integration**: Fetch project details directly from JIRA tickets
- **Phase Selection**: Choose specific project phases (Requirements, Design, Development, Testing, Deployment)
- **Smart Complexity Detection**: Specialized algorithms for React Native, mobile development, and enterprise projects

### Advanced Capabilities
- **React Native Expertise**: Accurate estimates for RN upgrades, native migrations, and dependency updates
- **Visual Analytics**: Interactive charts showing phase breakdown and time distribution
- **Risk Assessment**: AI identifies potential risk factors and provides confidence ratings
- **Flexible Workflows**: Rule-based fallback when AI is unavailable

### AI Workflow (Beta)
- **Solution Design Generation**: AI creates technical designs from JIRA requirements
- **Code Generation**: Automated code generation from approved designs
- **Codebase Analysis**: Analyze existing codebases for tech stack and patterns

## 📋 Prerequisites

- Python 3.7 or higher
- Azure OpenAI API access (optional, for AI features)
- JIRA API token (optional, for JIRA integration)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rithik1007/Esti-Mate.git
   cd Esti-Mate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the app**
   Open `http://localhost:5000` in your browser

## ⚙️ Configuration

Create a `.env` file with your credentials:

```env
# JIRA Configuration
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# Flask Configuration
SECRET_KEY=your-secret-key
```

## 🎯 Usage

### Basic Estimation
1. Enter a JIRA ticket number OR project description
2. Select phases you want to include
3. Choose AI-powered or rule-based estimation
4. Get detailed breakdown with visual charts

### AI Workflow
1. Navigate to "AI-Powered Workflow"
2. Generate solution designs from JIRA tickets
3. Get approval workflows for technical designs
4. Generate code from approved designs

## 📊 Estimation Accuracy

### React Native Projects
- **Minor upgrades (0.76.x → 0.77.x)**: 120-200 hours
- **Major upgrades (0.76.x → 0.79.x)**: 200-400 hours
- **Objective-C to Swift migration**: 80-200 hours per module
- **Native dependency updates**: 60-150 hours

### General Projects
- **Low Complexity**: 40-80 hours
- **Medium Complexity**: 80-160 hours
- **High Complexity**: 160-400+ hours

## 🏗️ Project Structure

```
Esti-Mate/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env.example                   # Environment template
├── ai_modules/                    # AI-powered modules
│   ├── ai_estimator.py           # Core AI estimation logic
│   ├── design_generator/         # Solution design generation
│   ├── code_generator/           # AI code generation
│   └── repo_analyzer/            # Codebase analysis
├── templates/                     # HTML templates
│   ├── index.html               # Main estimation interface
│   └── ai_workflow.html         # AI workflow interface
└── static/                       # CSS, JS, and assets
    ├── style.css
    └── script.js
```

## 🤖 AI Features

- **Intelligent Analysis**: Context-aware estimation based on project type
- **Risk Assessment**: Identifies potential blockers and complications
- **Confidence Scoring**: AI provides confidence levels for estimates
- **Specialized Knowledge**: Expert-level understanding of React Native, mobile development

## 🔧 API Endpoints

- `POST /estimate` - Generate project estimates
- `POST /generate-design` - Create solution designs
- `POST /generate-code` - Generate code from designs
- `POST /analyze-codebase` - Analyze existing codebases
- `GET /test-ai` - Test AI connectivity

## 🚧 Roadmap

- [ ] Machine learning model training on historical data
- [ ] Integration with more project management tools
- [ ] Team velocity and capacity planning
- [ ] Export to PDF/Excel
- [ ] Historical estimation accuracy tracking
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For questions or issues, please open a GitHub issue or contact the maintainers.

---

**Built with ❤️ for accurate project estimation**