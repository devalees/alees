import os
import json
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from typing import Any, Dict, Optional

class SecretsManager:
    """AWS Secrets Manager integration for Django settings."""
    
    def __init__(self):
        """Initialize the secrets manager with AWS credentials."""
        self.client = boto3.client(
            'secretsmanager',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.prefix = settings.AWS_SECRETS_PREFIX

    def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a secret from AWS Secrets Manager.
        
        Args:
            secret_name: The name of the secret to retrieve
            
        Returns:
            Dict containing the secret values or None if not found
        """
        try:
            full_secret_name = f"{self.prefix}{secret_name}"
            response = self.client.get_secret_value(SecretId=full_secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return None
            raise

    def create_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """
        Create a new secret in AWS Secrets Manager.
        
        Args:
            secret_name: The name of the secret
            secret_value: The secret values to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_secret_name = f"{self.prefix}{secret_name}"
            self.client.create_secret(
                Name=full_secret_name,
                SecretString=json.dumps(secret_value)
            )
            return True
        except ClientError:
            return False

    def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """
        Update an existing secret in AWS Secrets Manager.
        
        Args:
            secret_name: The name of the secret
            secret_value: The new secret values
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_secret_name = f"{self.prefix}{secret_name}"
            self.client.update_secret(
                SecretId=full_secret_name,
                SecretString=json.dumps(secret_value)
            )
            return True
        except ClientError:
            return False

    def delete_secret(self, secret_name: str) -> bool:
        """
        Delete a secret from AWS Secrets Manager.
        
        Args:
            secret_name: The name of the secret to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_secret_name = f"{self.prefix}{secret_name}"
            self.client.delete_secret(
                SecretId=full_secret_name,
                ForceDeleteWithoutRecovery=True
            )
            return True
        except ClientError:
            return False

    def rotate_secret(self, secret_name: str) -> bool:
        """
        Rotate a secret in AWS Secrets Manager.
        
        Args:
            secret_name: The name of the secret to rotate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_secret_name = f"{self.prefix}{secret_name}"
            self.client.rotate_secret(SecretId=full_secret_name)
            return True
        except ClientError:
            return False 