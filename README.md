# Infraware CLI 🚀

**Your AI-powered multi-cloud operations assistant for seamless cloud infrastructure management.**

Infraware CLI is an intelligent command-line interface that combines the power of AI with multi-cloud expertise to help you manage, deploy, and optimize your cloud infrastructure across Google Cloud Platform (GCP), Amazon Web Services (AWS), Microsoft Azure, and Docker environments.

## ✨ Features

### 🌐 Multi-Cloud Support
- **Google Cloud Platform (GCP)** - Complete project and resource management
- **Amazon Web Services (AWS)** - EC2, Lambda, billing, and more
- **Microsoft Azure** - Resource groups, deployments, and services
- **Docker** - Container management and orchestration

### 🤖 AI-Powered Operations
- Intelligent command interpretation and execution
- Natural language cloud operations
- Best practices recommendations
- Cost optimization suggestions
- Automated troubleshooting assistance

### 💻 Enhanced Terminal Experience
- **Smart Command Completion** - Context-aware autocompletion
- **Command History** - Persistent history with reverse search (Ctrl+R)
- **Shell Integration** - Execute shell commands alongside AI operations
- **Interactive Prompts** - Rich, colorful terminal interface

### 🛠️ Core Capabilities
- **Infrastructure Management** - Create, modify, and monitor cloud resources
- **Cost Analysis** - Track and optimize cloud spending across platforms
- **Security & IAM** - Manage permissions and access controls
- **Monitoring & Alerts** - Set up and manage cloud monitoring
- **Container Operations** - Docker and Kubernetes management
- **Multi-cloud Strategy** - Best practices for hybrid cloud deployments

## 📦 Installation

### Prerequisites
Make sure you have `pipx` installed on your system:

```bash
# Install pipx if you haven't already
pip install pipx
```

### Install Infraware CLI
```bash
pipx install git+https://github.com/Infraware-dev/CLI.git
```

## 🔑 API Key Setup

To use Infraware CLI, you'll need an **Anthropic API key**. You can get one from the [Anthropic Console](https://console.anthropic.com/).

**Note:** Additional AI providers are coming soon! Stay tuned for more options.

## 🚀 Quick Start

Once installed, launch the Infraware CLI:

```bash
ifw
```

You'll be greeted with an interactive terminal where you can:

### Natural Language Commands
```bash
|>| user@hostname:~ List all my GCP projects
|>| user@hostname:~ Show me AWS EC2 instances in us-east-1
|>| user@hostname:~ Check my cloud costs for this month
|>| user@hostname:~ Create a new Docker container for my web app
```

### Direct Shell Commands
```bash
|>| user@hostname:~ ls -la
|>| user@hostname:~ cd /path/to/project
|>| user@hostname:~ kubectl get pods
```

### Control Commands
- `clear` - Clear the terminal screen
- `reset` - Reset shell state to initial directory
- `exit` - Exit the CLI

## 💡 Example Use Cases

### Cloud Resource Management
```bash
# List all resources across clouds
Show me all my running instances across AWS and GCP

# Create infrastructure
Create a new VPC in AWS us-west-2 with public and private subnets

# Monitor costs
Compare my monthly spending between GCP and Azure
```

### Container Operations
```bash
# Docker management
List all running Docker containers and their resource usage

# Kubernetes operations
Deploy my web application to the production Kubernetes cluster

# Container optimization
Help me optimize my Docker images for better performance
```

### Troubleshooting & Monitoring
```bash
# Diagnose issues
My Lambda function is timing out, help me troubleshoot

# Set up monitoring
Create CloudWatch alarms for my EC2 instances

# Security audit
Review IAM permissions for my GCP service accounts
```

## ⌨️ Keyboard Shortcuts

- **Ctrl+R** - Reverse search through command history
- **Ctrl+L** - Clear the terminal screen
- **Ctrl+C** - Interrupt current operation
- **Ctrl+D** - Exit the CLI
- **Tab** - Smart command completion

## 🔧 Configuration

Infraware CLI automatically detects and uses your existing cloud credentials:

- **AWS** - Uses AWS CLI credentials 
- **GCP** - Uses gcloud CLI authentication
- **Azure** - Uses Azure CLI authentication
- **Docker** - Uses local Docker daemon

Make sure you're authenticated with your respective cloud providers before using Infraware CLI.

## 🎯 Command Examples

### Infrastructure Operations
```bash
# AWS Operations
Create an EC2 instance with Ubuntu 22.04 in us-east-1
List all my S3 buckets and their sizes
Set up Auto Scaling for my web servers

# GCP Operations
Show me all Compute Engine instances across all regions
Create a new Cloud Storage bucket with lifecycle policies
Deploy a Cloud Function for image processing

# Azure Operations
List all resource groups and their costs
Create a new App Service for my web application
Set up Azure Monitor for my virtual machines
```

### Cost Management
```bash
# Cost analysis
Show me my top 5 most expensive services this month
Compare costs between regions for my workloads
Suggest ways to reduce my cloud spending

# Billing alerts
Set up billing alerts for when I exceed $500/month
Show me cost trends for the last 6 months
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support (WIP)

- **Documentation**: [docs.infraware.dev](https://docs.infraware.dev)
- **Issues**: [GitHub Issues](https://github.com/Infraware-dev/CLI/issues)
- **Community**: [Join our Discord](https://discord.gg/infraware)

## 🚀 What's Next?

(WIP)

---

**Made with ❤️ by the Infraware team**

*Simplifying cloud operations, one command at a time.*