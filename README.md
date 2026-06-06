# Inventory Management System

A full-stack inventory management app built with **React + FastAPI + Supabase (PostgreSQL)**.

## Stack
- **Frontend**: React 18, Vite, Axios — runs on `http://localhost:3000`
- **Backend**: FastAPI, SQLAlchemy, Pydantic v2 — runs on `http://localhost:8000`
- **Database**: Supabase (PostgreSQL 17)

## Quick start

### 1. Database
Run `sql/schema.sql` in the Supabase SQL Editor to create the tables.

### 2. Backend
```bash
cd backend
# activate venv
..\.venv311\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```
Swagger UI: http://127.0.0.1:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:3000

## Features
- Category CRUD (create, edit, delete with confirmation)
- Item CRUD (name, SKU, category, quantity, price, status)
- Search items by name or SKU
- Filter items by category
- Stats dashboard (units, categories, stock value)
- Status badges (In Stock / Low Stock / Out of Stock)
- Toast notifications for all actions
- Loading spinner and error display
- Responsive layout (mobile + desktop)

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check |
| GET | /api/stats | Dashboard statistics |
| GET | /api/categories | List categories |
| POST | /api/categories | Create category |
| PUT | /api/categories/{id} | Update category |
| DELETE | /api/categories/{id} | Delete category |
| GET | /api/items | List items (filter: ?q=, ?category_id=) |
| POST | /api/items | Create item |
| PUT | /api/items/{id} | Update item |
| DELETE | /api/items/{id} | Delete item |
