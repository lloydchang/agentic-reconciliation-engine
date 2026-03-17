package bedrock

import (
	"encoding/json"
	"net/http"

	"github.com/gorilla/mux"
)

// BedrockHandler handles Bedrock API endpoints
type BedrockHandler struct {
	client *BedrockClient
}

// NewBedrockHandler creates a new Bedrock handler
func NewBedrockHandler(region string) (*BedrockHandler, error) {
	client, err := NewBedrockClient(region)
	if err != nil {
		return nil, err
	}

	return &BedrockHandler{
		client: client,
	}, nil
}

// RegisterRoutes registers Bedrock routes
func (h *BedrockHandler) RegisterRoutes(router *mux.Router) {
	// Model management endpoints
	router.HandleFunc("/models", h.handleListModels).Methods("GET")
	router.HandleFunc("/models/{modelId}", h.handleGetModel).Methods("GET")
	router.HandleFunc("/models/provider/{provider}", h.handleListModelsByProvider).Methods("GET")
	router.HandleFunc("/models/capability/{capability}", h.handleListModelsByCapability).Methods("GET")

	// Inference endpoints
	router.HandleFunc("/invoke", h.handleInvokeModel).Methods("POST")
	router.HandleFunc("/conversation", h.handleInvokeConversation).Methods("POST")

	// Validation endpoints
	router.HandleFunc("/validate/invoke", h.handleValidateInvokeRequest).Methods("POST")
	router.HandleFunc("/validate/conversation", h.handleValidateConversationRequest).Methods("POST")
}

// handleListModels handles listing all available models
func (h *BedrockHandler) handleListModels(w http.ResponseWriter, r *http.Request) {
	models := h.client.GetAvailableModels()

	response := map[string]interface{}{
		"models": models,
		"count":  len(models),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleGetModel handles getting a specific model
func (h *BedrockHandler) handleGetModel(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	modelID := vars["modelId"]

	model, err := h.client.GetModelByID(modelID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(model)
}

// handleListModelsByProvider handles listing models by provider
func (h *BedrockHandler) handleListModelsByProvider(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	provider := vars["provider"]

	models := h.client.ListModelsByProvider(provider)

	response := map[string]interface{}{
		"models":   models,
		"count":    len(models),
		"provider": provider,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleListModelsByCapability handles listing models by capability
func (h *BedrockHandler) handleListModelsByCapability(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	capability := vars["capability"]

	models := h.client.ListModelsByCapability(capability)

	response := map[string]interface{}{
		"models":     models,
		"count":      len(models),
		"capability": capability,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleInvokeModel handles model invocation
func (h *BedrockHandler) handleInvokeModel(w http.ResponseWriter, r *http.Request) {
	var request BedrockRequest
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate request
	if err := h.client.ValidateRequest(request); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Invoke model
	response, err := h.client.InvokeModel(r.Context(), request)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleInvokeConversation handles conversation invocation
func (h *BedrockHandler) handleInvokeConversation(w http.ResponseWriter, r *http.Request) {
	var request ConversationRequest
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validate request
	if err := h.client.ValidateConversationRequest(request); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Invoke conversation
	response, err := h.client.InvokeConversation(r.Context(), request)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleValidateInvokeRequest handles validation of invoke requests
func (h *BedrockHandler) handleValidateInvokeRequest(w http.ResponseWriter, r *http.Request) {
	var request BedrockRequest
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := h.client.ValidateRequest(request)
	response := map[string]interface{}{
		"valid": err == nil,
	}

	if err != nil {
		response["error"] = err.Error()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleValidateConversationRequest handles validation of conversation requests
func (h *BedrockHandler) handleValidateConversationRequest(w http.ResponseWriter, r *http.Request) {
	var request ConversationRequest
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	err := h.client.ValidateConversationRequest(request)
	response := map[string]interface{}{
		"valid": err == nil,
	}

	if err != nil {
		response["error"] = err.Error()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
