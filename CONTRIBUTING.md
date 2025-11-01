# Contributing to Myth Factory

Thank you for your interest in contributing to Myth Factory! This project aims to make mythology accessible through engaging AI-generated video content.

## 🎯 Project Vision

Myth Factory democratizes high-quality content creation by allowing anyone to transform written mythology stories into professional Instagram Reels using AI assistance.

## 🚀 How to Contribute

### 1. **Feature Improvements**
- Enhanced video effects and transitions
- Additional AI voice options
- Subtitle generation capabilities
- Direct social media integration

### 2. **Content & Assets**
- High-quality mythology artwork
- Background music compositions
- Story templates and examples
- Voice settings optimization

### 3. **Documentation**
- Tutorial videos
- User guides improvements
- Translation to other languages
- API documentation

### 4. **Bug Fixes & Optimization**
- Performance improvements
- Error handling enhancements
- Cross-platform compatibility
- Memory optimization

## 🛠️ Development Setup

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/myth-factory.git
   cd myth-factory
   ```

3. **Set up environment**:
   ```bash
   python -m venv myth-factory-env
   source myth-factory-env/bin/activate  # On Windows: myth-factory-env\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure API keys**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Test the setup**:
   ```bash
   python process_stories.py
   ```

## 📝 Code Standards

### **Python Code Style**
- Follow PEP 8 style guide
- Use type hints where appropriate
- Include docstrings for functions and classes
- Add comments for complex logic

### **Commit Messages**
- Use clear, descriptive commit messages
- Format: `type(scope): description`
- Examples:
  - `feat(video): add subtitle generation`
  - `fix(audio): resolve volume mixing issue`
  - `docs(readme): update installation steps`

### **Testing**
- Test with different story types and lengths
- Verify output quality and format
- Check error handling and edge cases
- Test on different operating systems if possible

## 🎨 Asset Guidelines

### **Images**
- High resolution (1080p+)
- Mythology/spiritual themes
- Public domain or Creative Commons licensed
- Diverse cultural representation

### **Audio**
- Royalty-free background music
- Ambient/cinematic style preferred
- Good quality audio files
- Appropriate for storytelling

## 📚 Documentation

### **Required for New Features**
- Update relevant README sections
- Add to QUICK_START.md if user-facing
- Include in PROJECT_DOCUMENTATION.md
- Update .env.example if new settings

### **Code Documentation**
- Docstrings for all new functions
- Type hints for parameters and returns
- Inline comments for complex logic
- Update existing docs if changing behavior

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment details**:
   - Operating system
   - Python version
   - Package versions

2. **Steps to reproduce**:
   - Exact commands run
   - Input files used
   - Expected vs actual behavior

3. **Error information**:
   - Full error messages
   - Log file contents (logs/run.log)
   - Screenshots if applicable

## 💡 Feature Requests

For new features, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and problem it solves
3. **Provide examples** of desired functionality
4. **Consider implementation** complexity and scope

## 🔄 Pull Request Process

1. **Create feature branch** from main
2. **Make your changes** following code standards
3. **Test thoroughly** with various inputs
4. **Update documentation** as needed
5. **Submit pull request** with clear description

### **Pull Request Template**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Tested with sample stories
- [ ] Verified output quality
- [ ] Checked error handling
- [ ] Updated documentation

## Screenshots/Examples
Include any relevant screenshots or example outputs
```

## 🎖️ Recognition

Contributors will be:
- Listed in project credits
- Mentioned in release notes
- Given appropriate attribution in documentation

## 📞 Community

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code Review**: All pull requests require review

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for helping make mythology more accessible through technology! 🏛️✨
