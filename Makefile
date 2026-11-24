# Swahili Concern Classification System
# Makefile for common development commands

# Backend
install-backend:
	cd backend && pip install -r requirements.txt

run-backend:
	cd backend && source venv/Scripts/activate && python app.py

# Database
setup-db:
	psql -U postgres -p 5433 -c "CREATE USER concern_user WITH PASSWORD 'password123';"
	psql -U postgres -p 5433 -c "CREATE DATABASE concern_db OWNER concern_user;"
	psql -U postgres -p 5433 -c "GRANT ALL PRIVILEGES ON DATABASE concern_db TO concern_user;"
	psql -U concern_user -d concern_db -p 5433 -f backend/database/schema.sql
	@echo "Database setup complete"

reset-db:
	psql -U postgres -p 5433 -c "DROP DATABASE IF EXISTS concern_db;"
	psql -U postgres -p 5433 -c "CREATE DATABASE concern_db OWNER concern_user;"
	psql -U concern_user -d concern_db -p 5433 -f backend/database/schema.sql
	@echo "Database reset complete"

check-db:
	psql -U concern_user -d concern_db -p 5433 -c "\dt"
	psql -U concern_user -d concern_db -p 5433 -c "SELECT * FROM categories;"

# Dashboard
install-dashboard:
	cd dashboard/cbo-dashboard && npm install

run-dashboard:
	cd dashboard/cbo-dashboard && npm start

# Mobile
install-mobile:
	cd mobile/ConcernApp && npm install

run-mobile:
	cd mobile/ConcernApp && npx expo start

# Data preparation
prepare-data:
	cd backend && source venv/Scripts/activate && python ../scripts/prepare_data.py

# Git helpers
status:
	git status

log:
	git log --oneline --graph --all

.PHONY: install-backend run-backend setup-db reset-db check-db install-dashboard run-dashboard install-mobile run-mobile prepare-data status log
