#!/usr/bin/env python3
"""
Security Analysis Handler

Cloud-specific operations handler for security analysis across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class SecurityHandler(ABC):
    """Abstract base class for cloud-specific security operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def check_network_security(self) -> List[Dict[str, Any]]:
        """Check network security configurations"""
        pass
    
    @abstractmethod
    def check_identity_security(self) -> List[Dict[str, Any]]:
        """Check identity and access management security"""
        pass
    
    @abstractmethod
    def check_data_security(self) -> List[Dict[str, Any]]:
        """Check data protection security"""
        pass
    
    @abstractmethod
    def check_infrastructure_security(self) -> List[Dict[str, Any]]:
        """Check infrastructure security"""
        pass
    
    @abstractmethod
    def check_application_security(self) -> List[Dict[str, Any]]:
        """Check application security"""
        pass
    
    @abstractmethod
    def check_compliance(self) -> List[Dict[str, Any]]:
        """Check compliance against policies"""
        pass

class AWSSecurityHandler(SecurityHandler):
    """AWS-specific security operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'ec2': boto3.client('ec2', region_name=self.region),
                'iam': boto3.client('iam', region_name=self.region),
                's3': boto3.client('s3', region_name=self.region),
                'rds': boto3.client('rds', region_name=self.region),
                'securityhub': boto3.client('securityhub', region_name=self.region),
                'guardduty': boto3.client('guardduty', region_name=self.region),
                'config': boto3.client('config', region_name=self.region),
                'macie': boto3.client('macie2', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def check_network_security(self) -> List[Dict[str, Any]]:
        """Check AWS network security configurations"""
        try:
            issues = []
            
            # Check VPC configurations
            vpcs = self.client['ec2'].describe_vpcs()
            for vpc in vpcs['Vpcs']:
                # Check if VPC has flow logs
                flow_logs = self.client['ec2'].describe_flow_logs(
                    Filters=[{'Name': 'resource-id', 'Values': [vpc['VpcId']]}]
                )
                
                if not flow_logs['FlowLogs']:
                    issues.append({
                        'title': 'VPC Flow Logs Disabled',
                        'description': f'VPC {vpc["VpcId"]} does not have flow logs enabled',
                        'risk_level': 'medium',
                        'resource_id': vpc['VpcId'],
                        'resource_name': vpc.get('Tags', [{}])[0].get('Value', vpc['VpcId']),
                        'severity_score': 0.6,
                        'impact_score': 0.7,
                        'likelihood_score': 0.5,
                        'affected_assets': [vpc['VpcId']],
                        'remediation_steps': [
                            'Enable VPC flow logs for network traffic monitoring',
                            'Configure appropriate log retention period',
                            'Set up CloudWatch log group for flow logs'
                        ],
                        'compliance_references': ['CIS AWS Foundations Benchmark 4.3'],
                        'threat_type': 'MISCONFIGURATION'
                    })
            
            # Check security groups
            security_groups = self.client['ec2'].describe_security_groups()
            for sg in security_groups['SecurityGroups']:
                # Check for overly permissive rules
                for rule in sg['IpPermissions']:
                    if rule.get('IpRanges') and any(ip['CidrIp'] == '0.0.0.0/0' for ip in rule['IpRanges']):
                        if rule.get('FromPort') in [22, 3389] or rule.get('IpProtocol') == '-1':
                            issues.append({
                                'title': 'Overly Permissive Security Group Rule',
                                'description': f'Security group {sg["GroupId"]} allows unrestricted access',
                                'risk_level': 'high',
                                'resource_id': sg['GroupId'],
                                'resource_name': sg.get('GroupName', sg['GroupId']),
                                'severity_score': 0.8,
                                'impact_score': 0.9,
                                'likelihood_score': 0.7,
                                'affected_assets': [sg['GroupId']],
                                'remediation_steps': [
                                    'Restrict access to specific IP ranges',
                                    'Implement bastion host for administrative access',
                                    'Use VPN or AWS PrivateLink for secure access'
                                ],
                                'compliance_references': ['CIS AWS Foundations Benchmark 5.1'],
                                'threat_type': 'UNAUTHORIZED_ACCESS'
                            })
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to check AWS network security: {e}")
            return []
    
    def check_identity_security(self) -> List[Dict[str, Any]]:
        """Check AWS IAM security configurations"""
        try:
            issues = []
            
            # Check password policy
            try:
                password_policy = self.client['iam'].get_account_password_policy()
                
                if password_policy.get('MinimumPasswordLength', 0) < 14:
                    issues.append({
                        'title': 'Weak Password Policy',
                        'description': 'IAM password policy requires less than 14 characters',
                        'risk_level': 'medium',
                        'resource_id': 'iam-password-policy',
                        'resource_name': 'IAM Password Policy',
                        'severity_score': 0.6,
                        'impact_score': 0.7,
                        'likelihood_score': 0.5,
                        'affected_assets': ['IAM Users'],
                        'remediation_steps': [
                            'Set minimum password length to 14 characters',
                            'Enable password complexity requirements',
                            'Enable password reuse prevention'
                        ],
                        'compliance_references': ['CIS AWS Foundations Benchmark 1.1'],
                        'threat_type': 'UNAUTHORIZED_ACCESS'
                    })
                
                if not password_policy.get('RequireLowercaseCharacters', False):
                    issues.append({
                        'title': 'Missing Password Complexity Requirements',
                        'description': 'IAM password policy does not require lowercase characters',
                        'risk_level': 'medium',
                        'resource_id': 'iam-password-policy',
                        'resource_name': 'IAM Password Policy',
                        'severity_score': 0.5,
                        'impact_score': 0.6,
                        'likelihood_score': 0.4,
                        'affected_assets': ['IAM Users'],
                        'remediation_steps': [
                            'Enable lowercase character requirement',
                            'Enable uppercase character requirement',
                            'Enable numeric character requirement',
                            'Enable symbol character requirement'
                        ],
                        'compliance_references': ['CIS AWS Foundations Benchmark 1.1'],
                        'threat_type': 'UNAUTHORIZED_ACCESS'
                    })
                    
            except self.client['iam'].exceptions.NoSuchEntityException:
                issues.append({
                    'title': 'No Password Policy Configured',
                    'description': 'IAM account does not have a password policy configured',
                    'risk_level': 'high',
                    'resource_id': 'iam-password-policy',
                    'resource_name': 'IAM Password Policy',
                    'severity_score': 0.8,
                    'impact_score': 0.9,
                    'likelihood_score': 0.6,
                    'affected_assets': ['IAM Users'],
                    'remediation_steps': [
                        'Create and configure IAM password policy',
                        'Set minimum password length to 14 characters',
                        'Enable password complexity requirements',
                        'Enable password reuse prevention'
                    ],
                    'compliance_references': ['CIS AWS Foundations Benchmark 1.1'],
                    'threat_type': 'UNAUTHORIZED_ACCESS'
                })
            
            # Check for users with console access and MFA
            users = self.client['iam'].list_users()
            for user in users['Users']:
                login_profile = None
                try:
                    login_profile = self.client['iam'].get_login_profile(UserName=user['UserName'])
                except self.client['iam'].exceptions.NoSuchEntityException:
                    continue  # No console access
                
                # Check MFA devices
                mfa_devices = self.client['iam'].list_mfa_devices(UserName=user['UserName'])
                if not mfa_devices['MFADevices']:
                    issues.append({
                        'title': 'User Without MFA',
                        'description=f'User {user["UserName"]} has console access without MFA enabled',
                        'risk_level': 'high',
                        'resource_id': user['UserId'],
                        'resource_name': user['UserName'],
                        'severity_score': 0.8,
                        'impact_score': 0.8,
                        'likelihood_score': 0.6,
                        'affected_assets': [user['UserName']],
                        'remediation_steps': [
                            'Enable MFA for this user account',
                            'Enforce MFA requirement for all IAM users',
                            'Consider using hardware MFA tokens for privileged accounts'
                        ],
                        'compliance_references': ['CIS AWS Foundations Benchmark 1.3'],
                        'threat_type': 'UNAUTHORIZED_ACCESS'
                    })
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to check AWS identity security: {e}")
            return []
    
    def check_data_security(self) -> List[Dict[str, Any]]:
        """Check AWS data protection security"""
        try:
            issues = []
            
            # Check S3 bucket encryption
            buckets = self.client['s3'].list_buckets()
            for bucket in buckets['Buckets']:
                try:
                    encryption = self.client['s3'].get_bucket_encryption(Bucket=bucket['Name'])
                except self.client['s3'].exceptions.ClientError:
                    issues.append({
                        'title': 'S3 Bucket Encryption Disabled',
                        'description=f'S3 bucket {bucket["Name"]} does not have encryption enabled',
                        'risk_level': 'medium',
                        'resource_id': bucket['Name'],
                        'resource_name': bucket['Name'],
                        'severity_score': 0.6,
                        'impact_score': 0.7,
                        'likelihood_score': 0.4,
                        'affected_assets': [bucket['Name']],
                        'remediation_steps': [
                            'Enable default encryption for the S3 bucket',
                            'Use AWS KMS managed keys or customer-managed keys',
                            'Review and update bucket policies for secure access'
                        ],
                        'compliance_references': ['CIS AWS Foundations Benchmark 2.1'],
                        'threat_type': 'DATA_BREACH'
                    })
                
                # Check bucket public access
                try:
                    public_access = self.client['s3'].get_public_access_block(Bucket=bucket['Name'])
                    if not public_access['PublicAccessBlockConfiguration'].get('BlockPublicAcls', True) or \
                       not public_access['PublicAccessBlockConfiguration'].get('BlockPublicPolicy', True):
                        issues.append({
                            'title': 'S3 Bucket Public Access Not Blocked',
                            'description=f'S3 bucket {bucket["Name"]} allows public access',
                            'risk_level': 'high',
                            'resource_id': bucket['Name'],
                            'resource_name': bucket['Name'],
                            'severity_score': 0.8,
                            'impact_score': 0.9,
                            'likelihood_score': 0.5,
                            'affected_assets': [bucket['Name']],
                            'remediation_steps': [
                                'Block all public access to the S3 bucket',
                                'Review bucket policies for any public access grants',
                                'Implement bucket-level access controls'
                            ],
                            'compliance_references': ['CIS AWS Foundations Benchmark 2.2'],
                            'threat_type': 'DATA_BREACH'
                        })
                except self.client['s3'].exceptions.ClientError:
                    issues.append({
                        'title': 'S3 Bucket Public Access Block Not Configured',
                        'description=f'S3 bucket {bucket["Name"]} does not have public access block configured',
                        'risk_level': 'medium',
                        'resource_id': bucket['Name'],
                        'resource_name': bucket['Name'],
                        'severity_score': 0.6,
                        'impact_score': 0.8,
                        'likelihood_score': 0.4,
                        'affected_assets': [bucket['Name']],
                        'remediation_steps': [
                            'Configure public access block for the S3 bucket',
                            'Block public ACLs and public policies',
                            'Review bucket access configurations'
                        ],
                        'compliance_references': ['CIS AWS Foundations Benchmark 2.2'],
                        'threat_type': 'DATA_BREACH'
                    })
            
            # Check RDS encryption
            db_instances = self.client['rds'].describe_db_instances()
            for db in db_instances['DBInstances']:
                if not db['StorageEncrypted']:
                    issues.append({
                        'title': 'RDS Instance Encryption Disabled',
                        'description=f'RDS instance {db["DBInstanceIdentifier"]} does not have encryption enabled',
                        'risk_level': 'medium',
                        'resource_id': db['DBInstanceIdentifier'],
                        'resource_name': db['DBInstanceIdentifier'],
                        'severity_score': 0.6,
                        'impact_score': 0.7,
                        'likelihood_score': 0.4,
                        'affected_assets': [db['DBInstanceIdentifier']],
                        'remediation_steps': [
                            'Enable encryption for the RDS instance',
                            'Use AWS KMS managed keys for encryption',
                            'Note: This requires snapshot and restore for existing instances'
                        ],
                        'compliance_references': ['CIS AWS Foundations Benchmark 2.4'],
                        'threat_type': 'DATA_BREACH'
                    })
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to check AWS data security: {e}")
            return []
    
    def check_infrastructure_security(self) -> List[Dict[str, Any]]:
        """Check AWS infrastructure security"""
        try:
            issues = []
            
            # Check EC2 instance security
            instances = self.client['ec2'].describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    # Check for public IP addresses
                    if instance.get('PublicIpAddress'):
                        # Check if instance is in a public subnet
                        if instance['State']['Name'] == 'running':
                            issues.append({
                                'title': 'EC2 Instance with Public IP',
                                'description=f'EC2 instance {instance["InstanceId"]} has a public IP address',
                                'risk_level': 'medium',
                                'resource_id': instance['InstanceId'],
                                'resource_name': instance.get('Tags', [{}])[0].get('Value', instance['InstanceId']),
                                'severity_score': 0.5,
                                'impact_score': 0.6,
                                'likelihood_score': 0.4,
                                'affected_assets': [instance['InstanceId']],
                                'remediation_steps': [
                                    'Consider using private subnets for instances',
                                    'Use NAT gateway for outbound internet access',
                                    'Implement security groups to restrict access'
                                ],
                                'compliance_references': ['CIS AWS Foundations Benchmark 4.1'],
                                'threat_type': 'UNAUTHORIZED_ACCESS'
                            })
                    
                    # Check for IAM instance profile
                    if not instance.get('IamInstanceProfile'):
                        issues.append({
                            'title': 'EC2 Instance Without IAM Role',
                            'description=f'EC2 instance {instance["InstanceId"]} does not have an IAM instance profile',
                            'risk_level': 'medium',
                            'resource_id': instance['InstanceId'],
                            'resource_name': instance.get('Tags', [{}])[0].get('Value', instance['InstanceId']),
                            'severity_score': 0.5,
                            'impact_score': 0.6,
                            'likelihood_score': 0.4,
                            'affected_assets': [instance['InstanceId']],
                            'remediation_steps': [
                                'Create and attach appropriate IAM instance profile',
                                'Follow least privilege principle for IAM roles',
                                'Use instance profiles for AWS service access'
                            ],
                            'compliance_references': ['CIS AWS Foundations Benchmark 4.4'],
                            'threat_type': 'UNAUTHORIZED_ACCESS'
                        })
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to check AWS infrastructure security: {e}")
            return []
    
    def check_application_security(self) -> List[Dict[str, Any]]:
        """Check AWS application security"""
        try:
            issues = []
            
            # Check for unencrypted application load balancers
            # This would require additional AWS clients for ELB
            # For now, we'll add a generic issue
            
            issues.append({
                'title': 'Application Security Review Required',
                'description='Review application security configurations including ALB, Lambda, and API Gateway',
                'risk_level': 'info',
                'resource_id': 'aws-applications',
                'resource_name': 'AWS Applications',
                'severity_score': 0.3,
                'impact_score': 0.4,
                'likelihood_score': 0.3,
                'affected_assets': ['ALB', 'Lambda', 'API Gateway'],
                'remediation_steps': [
                    'Review ALB security policies and SSL certificates',
                    'Check Lambda function permissions and VPC configurations',
                    'Validate API Gateway authorization and throttling settings'
                ],
                'compliance_references': ['AWS Security Best Practices'],
                'threat_type': 'MISCONFIGURATION'
            })
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to check AWS application security: {e}")
            return []
    
    def check_compliance(self) -> List[Dict[str, Any]]:
        """Check AWS compliance"""
        try:
            issues = []
            
            # Check for CloudTrail logging
            trails = self.client['cloudtrail'].describe_trails()
            if not trails['trailList']:
                issues.append({
                    'title': 'CloudTrail Not Enabled',
                    'description='AWS CloudTrail is not enabled for API logging',
                    'risk_level': 'high',
                    'resource_id': 'cloudtrail',
                    'resource_name': 'CloudTrail',
                    'severity_score': 0.8,
                    'impact_score': 0.8,
                    'likelihood_score': 0.6,
                    'affected_assets': ['AWS Account'],
                    'remediation_steps': [
                        'Enable CloudTrail in all regions',
                        'Configure log file validation',
                        'Send logs to CloudWatch Logs or S3 for long-term storage'
                    ],
                    'compliance_references': ['CIS AWS Foundations Benchmark 3.1'],
                    'threat_type': 'MISCONFIGURATION'
                })
            
            # Check for AWS Config
            try:
                config_recorders = self.client['config'].describe_configuration_recorders()
                if not config_recorders['ConfigurationRecorders']:
                    issues.append({
                        'title': 'AWS Config Not Enabled',
                        'description='AWS Config service is not enabled for configuration tracking',
                        'risk_level': 'medium',
                        'resource_id': 'aws-config',
                        'resource_name': 'AWS Config',
                        'severity_score': 0.6,
                        'impact_score': 0.7,
                        'likelihood_score': 0.5,
                        'affected_assets': ['AWS Account'],
                        'remediation_steps': [
                            'Enable AWS Config recorder',
                            'Configure appropriate recording frequency',
                            'Set up AWS Config rules for compliance checking'
                        ],
                        'compliance_references': ['CIS AWS Foundations Benchmark 1.6'],
                        'threat_type': 'MISCONFIGURATION'
                    })
            except Exception:
                pass
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to check AWS compliance: {e}")
            return []

# Simplified handlers for other providers
class AzureSecurityHandler(SecurityHandler):
    """Azure-specific security operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.security import SecurityCenter
            from azure.mgmt.monitor import MonitorManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'security': SecurityCenter(credential, "<subscription-id>"),
                'monitor': MonitorManagementClient(credential, "<subscription-id>")
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def check_network_security(self) -> List[Dict[str, Any]]:
        """Check Azure network security"""
        try:
            # Simplified Azure network security checks
            return [
                {
                    'title': 'Network Security Group Review Required',
                    'description='Review Azure Network Security Group configurations',
                    'risk_level': 'info',
                    'resource_id': 'azure-nsg',
                    'resource_name': 'NSG',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['NSG'],
                    'remediation_steps': [
                        'Review NSG rules for proper restrictions',
                        'Implement network segmentation',
                        'Enable flow logging for monitoring'
                    ],
                    'compliance_references': ['Azure Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check Azure network security: {e}")
            return []
    
    def check_identity_security(self) -> List[Dict[str, Any]]:
        """Check Azure identity security"""
        try:
            return [
                {
                    'title': 'Azure AD Security Review Required',
                    'description='Review Azure Active Directory security configurations',
                    'risk_level': 'info',
                    'resource_id': 'azure-ad',
                    'resource_name': 'Azure AD',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Azure AD'],
                    'remediation_steps': [
                        'Enable MFA for all users',
                        'Review privileged access assignments',
                        'Implement conditional access policies'
                    ],
                    'compliance_references': ['Azure Security Best Practices'],
                    'threat_type': 'UNAUTHORIZED_ACCESS'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check Azure identity security: {e}")
            return []
    
    def check_data_security(self) -> List[Dict[str, Any]]:
        """Check Azure data security"""
        try:
            return [
                {
                    'title': 'Azure Storage Security Review Required',
                    'description='Review Azure Storage account security configurations',
                    'risk_level': 'info',
                    'resource_id': 'azure-storage',
                    'resource_name': 'Storage Account',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Storage Account'],
                    'remediation_steps': [
                        'Enable encryption for storage accounts',
                        'Review access policies and permissions',
                        'Implement data classification and tagging'
                    ],
                    'compliance_references': ['Azure Security Best Practices'],
                    'threat_type': 'DATA_BREACH'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check Azure data security: {e}")
            return []
    
    def check_infrastructure_security(self) -> List[Dict[str, Any]]:
        """Check Azure infrastructure security"""
        try:
            return [
                {
                    'title': 'Azure VM Security Review Required',
                    'description='Review Azure virtual machine security configurations',
                    'risk_level': 'info',
                    'resource_id': 'azure-vm',
                    'resource_name': 'Virtual Machine',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['VM'],
                    'remediation_steps': [
                        'Review VM security configurations',
                        'Enable Azure Defender for Cloud',
                        'Implement proper network configurations'
                    ],
                    'compliance_references': ['Azure Security Best Practices'],
                    'threat_type': 'VULNERABILITY'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check Azure infrastructure security: {e}")
            return []
    
    def check_application_security(self) -> List[Dict[str, Any]]:
        """Check Azure application security"""
        try:
            return [
                {
                    'title': 'Azure App Service Security Review Required',
                    'description='Review Azure App Service security configurations',
                    'risk_level': 'info',
                    'resource_id': 'azure-app-service',
                    'resource_name': 'App Service',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['App Service'],
                    'remediation_steps': [
                        'Review App Service security settings',
                        'Enable SSL/TLS certificates',
                        'Implement proper authentication'
                    ],
                    'compliance_references': ['Azure Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check Azure application security: {e}")
            return []
    
    def check_compliance(self) -> List[Dict[str, Any]]:
        """Check Azure compliance"""
        try:
            return [
                {
                    'title': 'Azure Policy Compliance Review Required',
                    'description='Review Azure Policy compliance status',
                    'risk_level': 'info',
                    'resource_id': 'azure-policy',
                    'resource_name': 'Azure Policy',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Azure Resources'],
                    'remediation_steps': [
                        'Review Azure Policy assignments',
                        'Implement compliance monitoring',
                        'Configure remediation tasks'
                    ],
                    'compliance_references': ['Azure Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check Azure compliance: {e}")
            return []

class GCPSecurityHandler(SecurityHandler):
    """GCP-specific security operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import securitycenter_v1
            from google.cloud import monitoring_v3
            
            self.client = {
                'security': securitycenter_v1.SecurityCenterClient(),
                'monitoring': monitoring_v3.MetricServiceClient()
            }
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def check_network_security(self) -> List[Dict[str, Any]]:
        """Check GCP network security"""
        try:
            return [
                {
                    'title': 'GCP VPC Security Review Required',
                    'description='Review Google Cloud VPC security configurations',
                    'risk_level': 'info',
                    'resource_id': 'gcp-vpc',
                    'resource_name': 'VPC',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['VPC'],
                    'remediation_steps': [
                        'Review firewall rules',
                        'Enable VPC flow logs',
                        'Implement network segmentation'
                    ],
                    'compliance_references': ['GCP Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check GCP network security: {e}")
            return []
    
    def check_identity_security(self) -> List[Dict[str, Any]]:
        """Check GCP identity security"""
        try:
            return [
                {
                    'title': 'GCP IAM Security Review Required',
                    'description='Review Google Cloud IAM security configurations',
                    'risk_level': 'info',
                    'resource_id': 'gcp-iam',
                    'resource_name': 'IAM',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['IAM'],
                    'remediation_steps': [
                        'Review IAM roles and permissions',
                        'Implement least privilege principle',
                        'Enable audit logging'
                    ],
                    'compliance_references': ['GCP Security Best Practices'],
                    'threat_type': 'UNAUTHORIZED_ACCESS'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check GCP identity security: {e}")
            return []
    
    def check_data_security(self) -> List[Dict[str, Any]]:
        """Check GCP data security"""
        try:
            return [
                {
                    'title': 'GCP Storage Security Review Required',
                    'description='Review Google Cloud Storage security configurations',
                    'risk_level': 'info',
                    'resource_id': 'gcp-storage',
                    'resource_name': 'Cloud Storage',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Cloud Storage'],
                    'remediation_steps': [
                        'Review bucket permissions',
                        'Enable encryption at rest and in transit',
                        'Implement data classification'
                    ],
                    'compliance_references': ['GCP Security Best Practices'],
                    'threat_type': 'DATA_BREACH'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check GCP data security: {e}")
            return []
    
    def check_infrastructure_security(self) -> List[Dict[str, Any]]:
        """Check GCP infrastructure security"""
        try:
            return [
                {
                    'title': 'GCP Compute Security Review Required',
                    'description='Review Google Cloud Compute security configurations',
                    'risk_level': 'info',
                    'resource_id': 'gcp-compute',
                    'resource_name': 'Compute Engine',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Compute Engine'],
                    'remediation_steps': [
                        'Review VM security configurations',
                        'Enable OS Login',
                        'Implement proper firewall rules'
                    ],
                    'compliance_references': ['GCP Security Best Practices'],
                    'threat_type': 'VULNERABILITY'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check GCP infrastructure security: {e}")
            return []
    
    def check_application_security(self) -> List[Dict[str, Any]]:
        """Check GCP application security"""
        try:
            return [
                {
                    'title': 'GCP App Security Review Required',
                    'description='Review Google Cloud application security configurations',
                    'risk_level': 'info',
                    'resource_id': 'gcp-app',
                    'resource_name': 'GCP Applications',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['App Engine', 'Cloud Run'],
                    'remediation_steps': [
                        'Review application security settings',
                        'Implement proper authentication',
                        'Enable security scanning'
                    ],
                    'compliance_references': ['GCP Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check GCP application security: {e}")
            return []
    
    def check_compliance(self) -> List[Dict[str, Any]]:
        """Check GCP compliance"""
        try:
            return [
                {
                    'title': 'GCP Security Command Center Review Required',
                    'description='Review Google Cloud Security Command Center findings',
                    'risk_level': 'info',
                    'resource_id': 'gcp-scc',
                    'resource_name': 'Security Command Center',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['GCP Resources'],
                    'remediation_steps': [
                        'Review Security Command Center findings',
                        'Implement security health analytics',
                        'Configure asset inventory'
                    ],
                    'compliance_references': ['GCP Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check GCP compliance: {e}")
            return []

class OnPremSecurityHandler(SecurityHandler):
    """On-premise security operations"""
    
    def initialize_client(self) -> bool:
        try:
            logger.info("On-premise security handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def check_network_security(self) -> List[Dict[str, Any]]:
        """Check on-premise network security"""
        try:
            return [
                {
                    'title': 'On-Premise Network Security Review Required',
                    'description='Review on-premise network security configurations',
                    'risk_level': 'info',
                    'resource_id': 'onprem-network',
                    'resource_name': 'Network Infrastructure',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Firewalls', 'Switches', 'Routers'],
                    'remediation_steps': [
                        'Review firewall rules',
                        'Implement network segmentation',
                        'Enable network monitoring'
                    ],
                    'compliance_references': ['On-Premise Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check on-premise network security: {e}")
            return []
    
    def check_identity_security(self) -> List[Dict[str, Any]]:
        """Check on-premise identity security"""
        try:
            return [
                {
                    'title': 'On-Premise Identity Security Review Required',
                    'description='Review on-premise identity and access management',
                    'risk_level': 'info',
                    'resource_id': 'onprem-identity',
                    'resource_name': 'Identity Management',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Active Directory', 'LDAP'],
                    'remediation_steps': [
                        'Review user access permissions',
                        'Enable MFA for privileged accounts',
                        'Implement access reviews'
                    ],
                    'compliance_references': ['On-Premise Security Best Practices'],
                    'threat_type': 'UNAUTHORIZED_ACCESS'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check on-premise identity security: {e}")
            return []
    
    def check_data_security(self) -> List[Dict[str, Any]]:
        """Check on-premise data security"""
        try:
            return [
                {
                    'title': 'On-Premise Data Security Review Required',
                    'description='Review on-premise data protection measures',
                    'risk_level': 'info',
                    'resource_id': 'onprem-data',
                    'resource_name': 'Data Storage',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Databases', 'File Servers'],
                    'remediation_steps': [
                        'Review data encryption status',
                        'Implement backup and recovery',
                        'Configure access controls'
                    ],
                    'compliance_references': ['On-Premise Security Best Practices'],
                    'threat_type': 'DATA_BREACH'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check on-premise data security: {e}")
            return []
    
    def check_infrastructure_security(self) -> List[Dict[str, Any]]:
        """Check on-premise infrastructure security"""
        try:
            return [
                {
                    'title': 'On-Premise Infrastructure Security Review Required',
                    'description='Review on-premise infrastructure security',
                    'risk_level': 'info',
                    'resource_id': 'onprem-infra',
                    'resource_name': 'Infrastructure',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Servers', 'VMs'],
                    'remediation_steps': [
                        'Review server hardening status',
                        'Implement patch management',
                        'Configure monitoring and alerting'
                    ],
                    'compliance_references': ['On-Premise Security Best Practices'],
                    'threat_type': 'VULNERABILITY'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check on-premise infrastructure security: {e}")
            return []
    
    def check_application_security(self) -> List[Dict[str, Any]]:
        """Check on-premise application security"""
        try:
            return [
                {
                    'title': 'On-Premise Application Security Review Required',
                    'description='Review on-premise application security',
                    'risk_level': 'info',
                    'resource_id': 'onprem-app',
                    'resource_name': 'Applications',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['Web Servers', 'Application Servers'],
                    'remediation_steps': [
                        'Review application configurations',
                        'Implement security scanning',
                        'Configure secure coding practices'
                    ],
                    'compliance_references': ['On-Premise Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check on-premise application security: {e}")
            return []
    
    def check_compliance(self) -> List[Dict[str, Any]]:
        """Check on-premise compliance"""
        try:
            return [
                {
                    'title': 'On-Premise Compliance Review Required',
                    'description='Review on-premise compliance status',
                    'risk_level': 'info',
                    'resource_id': 'onprem-compliance',
                    'resource_name': 'Compliance',
                    'severity_score': 0.3,
                    'impact_score': 0.4,
                    'likelihood_score': 0.3,
                    'affected_assets': ['All Systems'],
                    'remediation_steps': [
                        'Review compliance policies',
                        'Implement audit logging',
                        'Conduct regular assessments'
                    ],
                    'compliance_references': ['On-Premise Security Best Practices'],
                    'threat_type': 'MISCONFIGURATION'
                }
            ]
        except Exception as e:
            logger.error(f"Failed to check on-premise compliance: {e}")
            return []

def get_security_handler(provider: str, region: str = "us-west-2") -> SecurityHandler:
    """Get appropriate security handler"""
    handlers = {
        'aws': AWSSecurityHandler,
        'azure': AzureSecurityHandler,
        'gcp': GCPSecurityHandler,
        'onprem': OnPremSecurityHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
