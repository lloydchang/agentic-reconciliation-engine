package main

import (
    "fmt"
    "os"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Println("Usage: <skill> <input>")
        os.Exit(1)
    }
    input := os.Args[1]
    fmt.Println("feature-flag-manager Go Skill Output for input:", input)
}

