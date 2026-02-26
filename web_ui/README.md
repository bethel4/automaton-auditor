# Automaton Auditor Web UI

Interactive web interface for testing and visualizing the Digital Courtroom audit process.

## 🚀 Quick Start

### Option 1: Use the launch script (Recommended)
```bash
# From the project root directory
python run_ui.py
```

### Option 2: Manual launch
```bash
# Install web dependencies
uv sync --optional web

# Navigate to web UI directory
cd web_ui

# Launch Streamlit
streamlit run app.py
```

The web interface will open automatically in your browser at `http://localhost:8501`

## 🎛️ Features

### Interactive Audit Configuration
- **Repository Input**: Enter any GitHub repository URL
- **Report Path**: Specify PDF or markdown report location
- **Advanced Options**: Enable tracing, debug mode

### Real-Time Visualization
- **Progress Tracking**: Watch the audit process step-by-step
- **Evidence Display**: Organized view of forensic findings
- **Judicial Deliberations**: Separate views for each judge's analysis
- **Final Verdict**: Comprehensive Chief Justice report

### Multi-Tab Interface
1. **🔍 Evidence**: View all collected forensic evidence
2. **⚖️ Judicial Opinions**: See dialectical analysis from all three judges
3. **📋 Final Report**: Chief Justice synthesis and recommendations
4. **📄 Raw Data**: Complete JSON output for debugging

## 🎨 UI Features

### Visual Indicators
- **Color-coded scores**: Green (excellent), Yellow (good), Red (needs improvement)
- **Confidence meters**: Visual representation of evidence confidence
- **Persona cards**: Distinct styling for Prosecutor, Defense, and Tech Lead
- **Progress bars**: Real-time audit progress tracking

### Interactive Elements
- **Expandable sections**: Detailed evidence and opinion analysis
- **Metric displays**: Overall scores and criteria counts
- **Status indicators**: Real-time feedback on audit progress

## 📊 Data Visualization

### Evidence Display
- **Category organization**: Repo analysis, PDF analysis, vision analysis
- **Confidence scoring**: Visual confidence meters
- **Content preview**: Expandable code snippets and text
- **Location tracking**: File paths and evidence sources

### Judicial Analysis
- **Persona separation**: Distinct visual styling for each judge
- **Score visualization**: Color-coded scoring system
- **Argument display**: Detailed reasoning and citations
- **Evidence linking**: Cross-references to supporting evidence

### Final Report
- **Executive summary**: Overall assessment and scoring
- **Criteria breakdown**: Detailed analysis by dimension
- **Remediation plans**: Specific improvement recommendations
- **Dissent documentation**: Conflict resolution summaries

## 🔧 Configuration Options

### Repository Settings
- **GitHub URL**: Any public repository
- **Branch selection**: Defaults to main branch
- **Authentication**: Supports private repos with tokens

### Report Analysis
- **PDF support**: Automatic PDF parsing
- **Markdown support**: Direct markdown analysis
- **Cross-referencing**: Automatic claim verification

### Advanced Features
- **LangSmith tracing**: Enable detailed execution logging
- **Debug mode**: Extended error reporting and logs
- **Batch processing**: Queue multiple repositories

## 🐛 Troubleshooting

### Common Issues

**UI doesn't load:**
```bash
# Check dependencies
pip install streamlit plotly pandas

# Verify app.py location
ls web_ui/app.py
```

**Audit fails:**
```bash
# Check environment variables
cat .env

# Verify rubric.json exists
ls rubric.json
```

**Performance issues:**
- Use smaller repositories for testing
- Enable debug mode for detailed logging
- Check API key configuration

### Debug Mode
Enable debug mode in the sidebar to see:
- Detailed error messages
- Step-by-step execution logs
- Raw API responses
- State transitions

## 🎯 Use Cases

### Development Testing
- Test your own repository implementation
- Validate forensic evidence collection
- Verify judicial analysis quality

### Peer Auditing
- Audit other Week 2 submissions
- Compare evaluation approaches
- Identify implementation gaps

### Educational Demo
- Demonstrate multi-agent orchestration
- Show dialectical synthesis in action
- Explain forensic analysis protocols

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -e ".[web]"
EXPOSE 8501
CMD ["streamlit", "run", "web_ui/app.py"]
```

### Cloud Deployment
- **Streamlit Cloud**: Direct deployment from GitHub
- **Heroku**: Container-based deployment
- **AWS**: ECS or Lambda integration

## 📱 Mobile Support

The web UI is responsive and works on:
- **Desktop browsers**: Chrome, Firefox, Safari, Edge
- **Tablets**: iPad, Android tablets
- **Mobile phones**: iOS Safari, Android Chrome

## 🔒 Security Considerations

- **No data persistence**: Results are session-based
- **Sandboxed execution**: Git operations in temporary directories
- **API key security**: Environment variable configuration
- **Input validation**: Repository URL and file path sanitization

## 🎨 Customization

### Styling
Edit the CSS in `app.py` to customize:
- Color schemes and themes
- Card layouts and spacing
- Typography and fonts
- Brand elements

### Features
Extend the UI with:
- Additional visualization charts
- Export functionality (PDF, JSON)
- Historical audit tracking
- Comparison tools

## 📞 Support

For issues with the web UI:
1. Check the troubleshooting section
2. Enable debug mode for detailed logs
3. Review the console output in browser dev tools
4. Check the main project README for common setup issues
