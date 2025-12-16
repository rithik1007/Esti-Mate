# AI Project Estimator

An intelligent web application that estimates project work across different phases based on JIRA numbers or project descriptions.

## Features

- **Smart Analysis**: Analyzes project complexity based on keywords and description length
- **Phase Breakdown**: Estimates work for:
  - Requirements Gathering (15%)
  - Design & Architecture (20%)
  - Development & Coding (45%)
  - Testing & UAT (15%)
  - Deployment & Production (5%)
- **Visual Charts**: Interactive doughnut chart showing phase distribution
- **JIRA Integration**: Optional JIRA number input for tracking
- **Responsive Design**: Works on desktop and mobile devices

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Open your browser and go to `http://localhost:5000`

3. Enter your project details:
   - JIRA Number (optional)
   - Project Description (required)

4. Click "Generate Estimate" to get your project estimation

## Project Structure

```
ai-project-estimator/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── templates/
│   └── index.html     # Main web interface
└── static/
    ├── style.css      # CSS styles
    └── script.js      # JavaScript functionality
```

## Complexity Analysis

The system analyzes project complexity based on:

- **High Complexity Keywords**: integration, api, database, migration, security, authentication, microservice, complex, multiple systems
- **Medium Complexity Keywords**: crud, form, validation, report, dashboard, ui, frontend, backend
- **Description Length**: Longer descriptions indicate higher complexity

## Estimation Logic

- **Low Complexity**: 40 base hours
- **Medium Complexity**: 80 base hours  
- **High Complexity**: 160 base hours

Hours are distributed across phases using predefined weights.

## Future Enhancements

- Database integration for storing estimates
- JIRA API integration for automatic ticket analysis
- Machine learning model for improved accuracy
- Team velocity considerations
- Historical data analysis
- Export functionality (PDF, Excel)
- User authentication and project management