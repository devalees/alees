#!/bin/bash

# Create base file with header
echo "# Core Strategy" > docs/architecture/merged_core_strategy.md
echo "" >> docs/architecture/merged_core_strategy.md
echo "## Table of Contents" >> docs/architecture/merged_core_strategy.md
echo "" >> docs/architecture/merged_core_strategy.md

# Add table of contents
cat << 'EOF' >> docs/architecture/merged_core_strategy.md
1. [Configuration Management](#configuration-management)
2. [Security Strategy](#security-strategy)
3. [Secrets Management](#secrets-management)
4. [Development Setup](#development-setup)
5. [Localization Strategy](#localization-strategy)
6. [Validation Strategy](#validation-strategy)
7. [Monitoring Strategy](#monitoring-strategy)
8. [Deployment & CI/CD](#deployment--cicd)
9. [Feature Flags](#feature-flags)

---
EOF

# Configuration Management
echo -e "\n## Configuration Management\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/configuration_management_strategy.md >> docs/architecture/merged_core_strategy.md

# Security Strategy
echo -e "\n## Security Strategy\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/security_strategy.md >> docs/architecture/merged_core_strategy.md

# Secrets Management
echo -e "\n## Secrets Management\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/secrets_management.md >> docs/architecture/merged_core_strategy.md

# Development Setup
echo -e "\n## Development Setup\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/development_setup_guide.md >> docs/architecture/merged_core_strategy.md

# Localization Strategy
echo -e "\n## Localization Strategy\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/localization_strategy.md >> docs/architecture/merged_core_strategy.md

# Validation Strategy
echo -e "\n## Validation Strategy\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/validation_strategy.md >> docs/architecture/merged_core_strategy.md

# Monitoring Strategy
echo -e "\n## Monitoring Strategy\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/monitoring_strategy.md >> docs/architecture/merged_core_strategy.md

# Deployment & CI/CD
echo -e "\n## Deployment & CI/CD\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/deployment_strategy_and_ci_cd.md >> docs/architecture/merged_core_strategy.md

# Feature Flags
echo -e "\n## Feature Flags\n" >> docs/architecture/merged_core_strategy.md
cat docs/architecture/core/feature_flags.md >> docs/architecture/merged_core_strategy.md 