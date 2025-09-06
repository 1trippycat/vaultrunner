<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# VaultRunner - HashiCorp Vault Docker Integration Tool

This project is a comprehensive shell script tool for seamless integration between HashiCorp Vault and Docker environments.

## Architecture Principles

### 1. Security First
- Security is the primary concern in all design decisions
- Implement defense-in-depth strategies
- Never log or expose sensitive data
- Use secure defaults and fail-safe mechanisms

### 2. Modularity Principles
- **Avoid monolithic file structures at all costs**
- Practice logical and clean separation of concerns
- Create standalone files all classes/models and put them in a models folder, no matter how small
- Import/source modules rather than inline everything
- Use clear naming conventions to enable directory searching
- Keep functions focused on single responsibilities
- Avoid bringing in unnecessary context between modules

### 3. Security Third (Reinforcement)
- We are building a HashiCorp Vault integration - security is paramount
- Validate all inputs and sanitize outputs
- Use principle of least privilege
- Implement proper authentication and authorization

### 4. Documentation Standards
- Document for the brand new developer joining the project
- Focus on productivity and getting developers up to speed quickly
- If documentation doesn't help a new developer be productive, don't write it
- Include practical examples and common use cases
- Document security considerations and best practices

### 5. Communication Guidelines
- Be clear and concise in responses
- Avoid redundancy in conversations
- Assume users remember previously communicated information
- Focus on actionable information

### 6. Security Last (Final Check)
- Security should be designed into the application architecture
- Review all code changes for security implications
- Implement security testing and validation
- Regular security audits and reviews

## Technical Guidelines

- She wrapper language: Shell script  (bash)
- Script language: Python
- Target: Production-ready tool for managing secrets in containerized environments
- Support for Docker, Docker Compose, and Kubernetes YAML
- Implement proper error handling and validation
- Support both dry-run and production modes
- Include comprehensive logging and audit trails
- Install application globally in the file system so it can be ran from anywhere.  
