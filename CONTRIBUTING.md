# Contributing to Infraware CLI

Thank you for your interest in contributing to Infraware CLI! 🎉 We're excited to have you join our community of developers working to simplify cloud operations through AI-powered tooling.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Contributions](#making-contributions)
- [Code Guidelines](#code-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Areas for Contribution](#areas-for-contribution)
- [Security Considerations](#security-considerations)
- [Getting Help](#getting-help)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold these standards. Please report unacceptable behavior by opening an issue or contacting the maintainers directly.

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or higher** installed on your system
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** for version control
- A **GitHub account** for submitting contributions

### First-Time Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CLI.git
   cd CLI
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/Infraware-dev/CLI.git
   ```

## Development Setup

### Environment Setup

1. **Create a virtual environment**:
   ```bash
   uv venv
   ```

2. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   uv pip install .
   ```

4. **Verify installation**:
   ```bash
   ifw --help
   ```

### Development Workflow

1. **Keep your fork updated**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit them with clear, descriptive messages

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Making Contributions

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes**
- ✨ **New features**
- 📚 **Documentation improvements**
- 🧪 **Tests** (especially needed!)
- 🎨 **UI/UX improvements**
- 🔧 **Performance optimizations**

### Before You Start

1. **Check existing issues** to see if your idea or bug report already exists
2. **Open an issue** to discuss significant changes before implementing them
3. **Search existing pull requests** to avoid duplicating work

## Code Guidelines

### Code Style

We use **Ruff** for code formatting and linting. Please ensure your code follows these standards:

1. **Format your code** before committing:
   ```bash
   ruff format .
   ```

2. **Check for linting issues**:
   ```bash
   ruff check .
   ```

3. **Fix auto-fixable issues**:
   ```bash
   ruff check --fix .
   ```

### Code Quality Standards

- **Write clear, descriptive variable and function names**
- **Add docstrings** to all public functions and classes
- **Keep functions focused** and reasonably sized
- **Use type hints** where helpful for clarity
- **Follow Python PEP 8** conventions (enforced by Ruff)

### Commit Messages

Write clear, concise commit messages:

```
feat: add hetzner mcp support

- Implement Hetzner Cloud MCP integration
- Update documentation with Hetzner examples
```

**Format**: `<type>: <description>`

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Testing

> 🚧 **Note**: We're currently working on implementing a comprehensive test suite. This is a great area for contributions!

### Current Status

- Testing framework: **pytest** (planned)
- Test coverage goals: **80%+**
- Integration tests: **Coming soon**

## Pull Request Process

### Before Submitting

- [ ] Code follows the style guidelines (Ruff formatting)
- [ ] Self-review of the code completed
- [ ] Code is well-documented
- [ ] Tests added/updated (when testing framework is available)
- [ ] Documentation updated if needed

### PR Guidelines

1. **Use a clear, descriptive title**
2. **Fill out the PR template** completely
3. **Link related issues** using keywords (e.g., "Fixes #123")
4. **Provide context** about your changes
5. **Include screenshots** for UI changes
6. **Keep PRs focused** - one feature/fix per PR

### Review Process

1. **Automated checks** must pass (Ruff, future tests)
2. **Code review** by maintainers
3. **Address feedback** promptly and professionally
4. **Squash commits** if requested before merge

## Areas for Contribution

### High Priority

- 🧪 **Testing Infrastructure**: Help us build a robust test suite
- 📊 **Cost Optimization Features**: Enhanced cloud cost analysis and recommendations
- 🔍 **Error Handling**: Improve error messages and troubleshooting guidance
- 📖 **Documentation**: Examples, tutorials, and API documentation

### Cloud Provider Support

- **AWS**: Enhanced service coverage, new regions
- **GCP**: Advanced networking features, ML operations
- **Azure**: Container services, serverless functions
- **Multi-cloud**: Cross-cloud migration tools, unified dashboards

### AI & UX Improvements

- **Natural Language Processing**: Better command interpretation
- **Context Awareness**: Improved memory and learning capabilities
- **Terminal Experience**: Enhanced autocomplete, better error messages
- **Performance**: Faster response times, optimized cloud API calls

## Security Considerations

### Credential Handling

- **We don't store credentials**: Infraware CLI relies on existing cloud provider CLIs (AWS CLI, gcloud, Azure CLI) for authentication
- **No credential files**: Never commit API keys, tokens, or other sensitive information
- **Environment variables**: Use environment variables for any configuration that might contain sensitive data
- **Secure coding**: Follow secure coding practices, especially when handling user input

### Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT open a public issue**
2. **Email us directly** at: security@infraware.dev
3. **Provide detailed information** about the vulnerability
4. **Wait for our response** before disclosing publicly

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests, questions
- **GitHub Discussions**: General questions, ideas, community chat
- **Discord**: [Join our Discord](https://discord.com/invite/GNXqSMWB) for real-time chat

### Documentation

- **Project README**: Overview and quick start guide
- **Documentation**: [docs.infraware.dev](https://docs.infraware.dev) 

### Maintainer Response Times

- **Issues**: We aim to respond within 48 hours
- **Pull Requests**: Initial review within 72 hours
- **Security Issues**: Response within 24 hours

## Recognition

Contributors will be:

- 🏆 **Listed in CONTRIBUTORS.md**
- 🎉 **Mentioned in release notes** 
- 💫 **Featured on our website** 
- 🌟 **Invited to join** 

## Development Tips

### Local Development

```bash
# Quick development setup
git clone https://github.com/YOUR_USERNAME/CLI.git
cd CLI
uv venv && source .venv/bin/activate
uv add -e .
```

### Debugging

- Use `--verbose` flag for detailed output

## License

By contributing to Infraware CLI, you agree that your contributions will be licensed under the same [Apache-2.0 License](LICENSE) that covers the project.

---

## 🚀 Ready to Contribute?

1. Pick an issue labeled `good first issue` or `help wanted`
2. Comment on the issue to let us know you're working on it
3. Fork, code, test, and submit a PR
4. Celebrate your contribution! 🎉

**Questions?** Don't hesitate to ask in issues or discussions. We're here to help make your contribution experience smooth and enjoyable.

---

**Happy coding! 💻✨**

*Made with ❤️ by the Infraware community*
