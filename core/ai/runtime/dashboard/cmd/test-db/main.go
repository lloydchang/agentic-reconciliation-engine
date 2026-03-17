package main

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	db, err := sql.Open("sqlite3", "/tmp/dashboard.db")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Test basic query
	var count int
	err = db.QueryRow("SELECT COUNT(*) FROM agents").Scan(&count)
	if err != nil {
		log.Fatal("Query failed:", err)
	}
	fmt.Printf("Total agents: %d\n", count)

	// Test status query
	var running, idle, errored, stopped int64
	err = db.QueryRow("SELECT COUNT(*) FROM agents WHERE status = 'running'").Scan(&running)
	if err != nil {
		log.Fatal("Running query failed:", err)
	}
	
	err = db.QueryRow("SELECT COUNT(*) FROM agents WHERE status = 'idle'").Scan(&idle)
	if err != nil {
		log.Fatal("Idle query failed:", err)
	}
	
	err = db.QueryRow("SELECT COUNT(*) FROM agents WHERE status = 'errored'").Scan(&errored)
	if err != nil {
		log.Fatal("Errored query failed:", err)
	}
	
	err = db.QueryRow("SELECT COUNT(*) FROM agents WHERE status = 'stopped'").Scan(&stopped)
	if err != nil {
		log.Fatal("Stopped query failed:", err)
	}

	fmt.Printf("Running: %d, Idle: %d, Errored: %d, Stopped: %d\n", running, idle, errored, stopped)
}
