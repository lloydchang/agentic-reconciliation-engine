#!/bin/bash
# Build Docker images for backend and frontend
docker build -t backstage-temporal-backend ./backend
docker build -t backstage-temporal-frontend ./frontend
