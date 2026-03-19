package ws

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/gorilla/websocket"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/models"
	"go.uber.org/zap"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for now
	},
}

type Hub struct {
	clients    map[*Client]bool
	broadcast  chan []byte
	register   chan *Client
	unregister chan *Client
	logger     *zap.Logger
}

type Client struct {
	hub  *Hub
	conn *websocket.Conn
	send chan []byte
}

type Message struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}

func NewHub(logger *zap.Logger) *Hub {
	return &Hub{
		clients:    make(map[*Client]bool),
		broadcast:  make(chan []byte),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		logger:     logger,
	}
}

func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			h.clients[client] = true
			h.logger.Info("Client connected", zap.Int("total_clients", len(h.clients)))

		case client := <-h.unregister:
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.send)
				h.logger.Info("Client disconnected", zap.Int("total_clients", len(h.clients)))
			}

		case message := <-h.broadcast:
			for client := range h.clients {
				select {
				case client.send <- message:
				default:
					close(client.send)
					delete(h.clients, client)
				}
			}
		}
	}
}

func (h *Hub) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("WebSocket upgrade error:", err)
		return
	}

	client := &Client{
		hub:  h,
		conn: conn,
		send: make(chan []byte, 256),
	}
	client.hub.register <- client

	go client.writePump()
	go client.readPump()
}

func (c *Client) readPump() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()

	for {
		_, message, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("WebSocket error: %v", err)
			}
			break
		}

		// Handle incoming messages if needed
		log.Printf("Received message: %s", message)
	}
}

func (c *Client) writePump() {
	defer c.conn.Close()

	for {
		select {
		case message, ok := <-c.send:
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := c.conn.WriteMessage(websocket.TextMessage, message); err != nil {
				log.Printf("WebSocket write error: %v", err)
				return
			}
		}
	}
}

// Broadcast methods
func (h *Hub) BroadcastAgentStatus(agent models.Agent) {
	message := Message{
		Type: "agent_status",
		Data: agent,
	}

	data, err := json.Marshal(message)
	if err != nil {
		h.logger.Error("Failed to marshal agent status", zap.Error(err))
		return
	}

	select {
	case h.broadcast <- data:
	default:
		// Channel is full, drop the message
	}
}

func (h *Hub) BroadcastActivity(activity models.Activity) {
	message := Message{
		Type: "activity",
		Data: activity,
	}

	data, err := json.Marshal(message)
	if err != nil {
		h.logger.Error("Failed to marshal activity", zap.Error(err))
		return
	}

	select {
	case h.broadcast <- data:
	default:
		// Channel is full, drop the message
	}
}

func (h *Hub) BroadcastMetrics(metrics models.SystemMetrics) {
	message := Message{
		Type: "metrics",
		Data: metrics,
	}

	data, err := json.Marshal(message)
	if err != nil {
		h.logger.Error("Failed to marshal metrics", zap.Error(err))
		return
	}

	select {
	case h.broadcast <- data:
	default:
		// Channel is full, drop the message
	}
}
