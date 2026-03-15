--- 
name: log-classifier 
description: Categorize operational logs into structured buckets. Triggers: user provides logs for analysis. 
tools: 
  - bash 
  - computer 
--- 

# Log Classifier Skill 

Analyze application and system logs to classify them into operational categories. 

## Inputs 
Raw log lines or log files. 

## Process 
1. Parse log entries 
2. Identify patterns (errors, warnings, info) 
3. Classify by type (application error, network issue, etc.) 
4. Assign severity and suggest actions 

## Outputs 
Categorized logs with classification, severity, and recommendations. 

## Examples 
Input: "2023-10-01 10:00:00 ERROR Failed to connect to database" 
Output: Category: Database connectivity, Severity: High, Action: Check DB service 

## Output Format 
[ 
  { 
    "log": "original log line", 
    "category": "error type", 
    "severity": "low|medium|high", 
    "suggested_action": "description" 
  } 
] 

