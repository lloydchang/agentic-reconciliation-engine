package notifier
import ("encoding/json"; "fmt")

func GenerateTeamsApprovalCard(workflowID string, resourceID string) string {
	card := map[string]interface{}{
		"type": "AdaptiveCard",
		"version": "1.4",
		"body": []map[string]interface{}{
			{"type": "TextBlock", "text": "⚠️ Security Drift Detected", "weight": "bolder"},
			{"type": "TextBlock", "text": fmt.Sprintf("Resource: %s", resourceID)},
		},
		"actions": []map[string]interface{}{
			{"type": "Action.Submit", "title": "Approve", "data": map[string]interface{}{"action": "approve"}},
		},
	}
	payload, _ := json.Marshal(card)
	return string(payload)
}
