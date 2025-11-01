# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

The History Reels team takes security seriously. If you discover a security vulnerability, please follow these guidelines:

### 🔒 **How to Report**

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please:

1. **Email**: Send details to `security@historyreels.dev` (if applicable) or
2. **GitHub Security**: Use GitHub's private security advisory feature
3. **Direct Contact**: Contact the maintainers through GitHub direct message

### 📝 **What to Include**

Please provide:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** assessment
- **Suggested fix** (if you have one)
- **Your contact information** for follow-up

### 🛡️ **Security Considerations**

### **API Key Protection**
- **Never commit API keys** to version control
- **Use .env files** that are gitignored
- **Rotate keys regularly** for production use
- **Use environment variables** in production

### **Input Validation**
- Story files are read as text only
- Image files are processed by MoviePy (trusted library)
- No code execution from user inputs
- File type validation prevents malicious uploads

### **External Dependencies**
- All dependencies are from trusted sources (PyPI)
- Regular dependency updates recommended
- Virtual environment isolation

### **AI API Security**
- API requests are made over HTTPS
- No sensitive data sent to AI services
- User content is processed according to service ToS

## 🔧 **Best Practices for Users**

### **Environment Security**
```bash
# Use virtual environments
python -m venv history-reels-env
source history-reels-env/bin/activate

# Keep dependencies updated
pip install --upgrade -r requirements.txt

# Secure your API keys
chmod 600 .env  # Restrict file permissions
```

### **Content Security**
- Don't process sensitive or private content
- Be aware that AI services may store data temporarily
- Review AI service privacy policies
- Use appropriate content for public sharing

### **System Security**
- Run in isolated environments
- Regular system updates
- Monitor logs for unusual activity
- Use strong API key management

## 🚨 **Known Security Considerations**

### **AI Service Data**
- **OpenAI**: Story content sent for script generation
- **ElevenLabs**: Generated scripts sent for voice synthesis
- **Recommendation**: Don't process highly sensitive content

### **File Processing**
- **Image Processing**: Uses MoviePy and ImageIO (trusted libraries)
- **File Types**: Limited to safe image formats (.jpg, .png, .webp)
- **Text Files**: Read as plain text only

### **Network Security**
- All API calls use HTTPS
- No local server components
- No incoming network connections

## 📋 **Security Checklist**

Before deployment or sharing:

- [ ] API keys are in .env file (not committed)
- [ ] .gitignore properly configured
- [ ] Dependencies are up to date
- [ ] Virtual environment is being used
- [ ] File permissions are appropriately set
- [ ] No sensitive content in repository

## 🔄 **Response Process**

When a security issue is reported:

1. **Acknowledgment** within 48 hours
2. **Initial assessment** within 1 week
3. **Fix development** timeline provided
4. **Coordinated disclosure** after fix is ready
5. **Public advisory** if necessary

## 📞 **Contact**

For security-related questions or concerns:

- **GitHub**: Use private security advisory feature
- **Issues**: For non-sensitive security discussions
- **Community**: General security best practices discussions

Thank you for helping keep History Reels secure! 🛡️
