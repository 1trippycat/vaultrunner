# VaultRunner Documentation

Welcome to the comprehensive VaultRunner documentation. This guide covers everything you need to know about using VaultRunner for secure secret management in containerized environments.

## 📚 Documentation Overview

- **[Getting Started](./getting-started.md)** - Installation and basic setup
- **[Core Concepts](./core-concepts.md)** - Namespaces, migration workflows, and architecture
- **[Command Reference](./commands.md)** - Complete command documentation
- **[Migration Guide](./migration.md)** - Migrating from existing systems
- **[Docker Integration](./docker.md)** - Docker and Docker Compose integration
- **[MCP Server Guide](./mcp-server.md)** - Model Context Protocol integration
- **[API Reference](./api.md)** - Developer API documentation
- **[Troubleshooting](./troubleshooting.md)** - Common issues and solutions

## 🚀 Quick Navigation

### For New Users
1. [Installation](./getting-started.md#installation)
2. [First Secrets](./getting-started.md#your-first-secrets)
3. [Basic Deployment](./docker.md#basic-deployment)

### For Migration
1. [From .env Files](./migration.md#env-files)
2. [From Docker Secrets](./migration.md#docker-secrets)
3. [From Kubernetes](./migration.md#kubernetes)

### For Development
1. [Local Setup](./getting-started.md#development-setup)
2. [API Reference](./api.md)
3. [Contributing Guidelines](./contributing.md)

## 🎯 Key Features

### 🔐 **Secret Management with Namespaces**
Organize secrets by project, environment, or team with full namespace support.

### 🔄 **Migration Tools**
Easy import from .env files, Docker secrets, docker-compose.yml, and Kubernetes.

### 📄 **Smart Templates**
Auto-generated Docker, Kubernetes, and deployment templates.

### 🚀 **Deployment Integration**
Deploy applications with automatic secret injection from Vault.

### 🤖 **MCP Server Ready**
Built for Model Context Protocol integration with AI assistants.

## 📖 Core Concepts

### Namespaces
VaultRunner uses namespaces to organize secrets:
```bash
# Different environments
vaultrunner secrets add db/password "dev123" --namespace myapp-dev
vaultrunner secrets add db/password "prod456" --namespace myapp-prod

# Shared secrets
vaultrunner secrets add api/external-key "shared123" --namespace shared
```

### Migration Workflow
```bash
# 1. Import existing secrets
vaultrunner import env .env --namespace myapp

# 2. Deploy with Vault integration
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml

# 3. Verify secrets are injected
docker compose logs app | grep -i vault
```

## 🐳 Docker Integration

VaultRunner works seamlessly with complex Docker Compose setups:

```yaml
# docker-compose.yml (main file)
name: myapp
include:
  - docker-compose.core-data.yml
  - docker-compose.ai-ml.yml
  - docker-compose.app.yml
```

### Deployment Examples
```bash
# Deploy with namespace
vaultrunner deploy --namespace production --compose-file docker-compose.yml

# Deploy with Vault sidecar
vaultrunner deploy --namespace myapp --sidecar --compose-file docker-compose.yml
```

## 🔧 Development & API

### Local Development
```bash
git clone https://github.com/1trippycat/core.git
cd core/vaultrunner
pip install -e .
```

### MCP Server Integration
```bash
# Run as MCP server
vaultrunner mcp-server --port 3000
```

## 🆘 Support & Community

- **📚 [Documentation](./)** - Complete documentation
- **🐛 [Issues](https://github.com/1trippycat/core/issues)** - Bug reports and feature requests
- **💬 [Discussions](https://github.com/1trippycat/core/discussions)** - Community discussions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**VaultRunner** - Simplifying HashiCorp Vault integration for modern containerized applications.