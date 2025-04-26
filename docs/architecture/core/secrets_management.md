# Secrets Management Process

## Overview

This document outlines the secrets management strategy for the Alees ERP system, using AWS Secrets Manager as the primary secrets storage solution.

## AWS Secrets Manager Integration

### Configuration

1. **AWS Credentials**
   - Set up AWS IAM user with appropriate permissions for Secrets Manager
   - Configure AWS credentials in environment variables:
     ```
     AWS_ACCESS_KEY_ID=your-access-key
     AWS_SECRET_ACCESS_KEY=your-secret-key
     AWS_REGION=your-region
     AWS_SECRETS_PREFIX=alees/
     ```

2. **Secret Naming Convention**
   - All secrets are prefixed with `alees/`
   - Format: `alees/{environment}/{service}/{secret-name}`
   - Example: `alees/prod/database/credentials`

### Secret Types

1. **Database Credentials**
   - Secret name: `database/credentials`
   - Contains: `username`, `password`, `host`, `port`, `dbname`

2. **API Keys**
   - Secret name: `api/{service-name}/key`
   - Contains: `api_key`, `api_secret`

3. **JWT Secrets**
   - Secret name: `jwt/credentials`
   - Contains: `secret_key`, `algorithm`

4. **Email Credentials**
   - Secret name: `email/credentials`
   - Contains: `host`, `port`, `username`, `password`

## Secret Rotation Process

### Automatic Rotation

1. **Database Credentials**
   - Rotate every 30 days
   - Process:
     1. Generate new credentials
     2. Update database user
     3. Update secret in AWS
     4. Update application configuration
     5. Verify connection with new credentials

2. **API Keys**
   - Rotate every 90 days
   - Process:
     1. Generate new key pair
     2. Update secret in AWS
     3. Update application configuration
     4. Verify API access

3. **JWT Secrets**
   - Rotate every 30 days
   - Process:
     1. Generate new secret
     2. Update secret in AWS
     3. Update application configuration
     4. Verify token generation

### Manual Rotation

1. **Emergency Rotation**
   - Triggered by security incidents
   - Process:
     1. Generate new credentials
     2. Update secret in AWS
     3. Update application configuration
     4. Verify functionality

2. **Scheduled Rotation**
   - Triggered by security policy
   - Process:
     1. Generate new credentials
     2. Update secret in AWS
     3. Update application configuration
     4. Verify functionality

## Implementation

### Using the Secrets Manager

```python
from core.secrets import SecretsManager

# Initialize the manager
secrets_manager = SecretsManager()

# Get a secret
database_creds = secrets_manager.get_secret('database/credentials')

# Create a new secret
secrets_manager.create_secret('api/new-service/key', {
    'api_key': 'new-key',
    'api_secret': 'new-secret'
})

# Update a secret
secrets_manager.update_secret('email/credentials', {
    'host': 'new-host',
    'port': 587,
    'username': 'new-user',
    'password': 'new-password'
})

# Rotate a secret
secrets_manager.rotate_secret('jwt/credentials')
```

### Integration with Django Settings

```python
# config/settings/prod.py
from core.secrets import SecretsManager

secrets_manager = SecretsManager()

# Load database credentials
db_creds = secrets_manager.get_secret('database/credentials')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_creds['dbname'],
        'USER': db_creds['username'],
        'PASSWORD': db_creds['password'],
        'HOST': db_creds['host'],
        'PORT': db_creds['port'],
    }
}
```

## Security Considerations

1. **Access Control**
   - Limit AWS IAM permissions to necessary actions
   - Use IAM roles for EC2 instances
   - Implement least privilege principle

2. **Audit Logging**
   - Enable AWS CloudTrail for Secrets Manager
   - Monitor secret access patterns
   - Alert on unusual access patterns

3. **Encryption**
   - All secrets are encrypted at rest
   - Use AWS KMS for encryption
   - Rotate KMS keys annually

4. **Backup and Recovery**
   - Regular backup of secrets
   - Document recovery procedures
   - Test recovery process quarterly

## Monitoring and Alerts

1. **Secret Access**
   - Monitor failed access attempts
   - Alert on unusual access patterns
   - Track secret usage metrics

2. **Rotation Status**
   - Monitor rotation success/failure
   - Alert on overdue rotations
   - Track rotation metrics

3. **Secret Health**
   - Monitor secret expiration
   - Alert on expiring secrets
   - Track secret lifecycle 