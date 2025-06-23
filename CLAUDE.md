# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important: Technology Stack Requirements

**ALWAYS use the correct technology for each part of the application:**
- **Frontend**: MUST use React (JavaScript/JSX) - located in `/frontend`
- **Backend**: MUST use Python with Flask - located in `/backend`
- **Database**: SQLAlchemy ORM with PostgreSQL (prod) or SQLite (dev)
- **Never mix technologies**: Do not use Python in frontend or JavaScript in backend

## Development Commands

### Frontend (React)
- `cd frontend && npm start` - Start development server (runs on localhost:3000)
- `cd frontend && npm run build` - Build for production
- `cd frontend && npm test` - Run test suite with Jest
- `cd frontend && npm install` - Install dependencies

### Backend (Flask)
- `cd backend && python app.py` - Start development server (runs on localhost:5000)
- `cd backend && python init_db.py` - Initialize database with tables
- `cd backend && pip install -r requirements.txt` - Install dependencies
- `cd backend && python -m venv venv && source venv/bin/activate` - Create and activate virtual environment (first time setup)

### Docker Deployment
- `docker-compose up --build` - Build and start all services
- `docker-compose down` - Stop all services
- Production deployment runs on port 80 with Nginx reverse proxy
- Services: `nginx` (reverse proxy), `frontend` (React), `backend` (Flask)

## Architecture Overview

This is a **GymMolly e-commerce order management system** with React frontend and Flask backend.

### System Architecture
- **Frontend**: React 18 with Bootstrap UI, handles order creation and management
- **Backend**: Flask REST API with SQLAlchemy ORM, manages orders and integrations
- **Database**: PostgreSQL (production), SQLite (development)
- **External APIs**: ShipStation (fulfillment), SendGrid (email notifications)
- **Deployment**: Docker Compose + Nginx reverse proxy

### Key Data Models
- `Orders` - Main order records with PO numbers and status
- `OrderItems` - Line items linking orders to products with quantities
- `ItemDetail` - Product catalog (SKU, size, flavor, price)
- `InventoryQuantity` - Current stock levels per product
- `ShippingAddresses` - Customer shipping information

### Core Workflows
1. **Order Creation**: OrderForm → OrderValidation → Backend API → ShipStation + SendGrid
2. **Inventory Management**: UpdateInventory component manages stock levels
3. **Address Management**: AddAddress/UpdateAddress components handle shipping info
4. **File Attachments**: Orders support PDF attachments via React Dropzone

### Environment Configuration
- Development: Uses `.env.development` with local SQLite
- Production: Uses `.env.production` with PostgreSQL
- Required variables: `DATABASE_URL`, `SS_CLIENT_ID`, `SS_CLIENT_SECRET`, `SS_STORE_ID`, `SENDGRID_API_KEY`, `SENDER_EMAIL`, `RECIPIENT_EMAIL`

### API Integration Details
- **ShipStation**: Creates orders and manages fulfillment via REST API
- **SendGrid**: Sends order confirmation emails to customers and admins
- **Authentication**: ShipStation uses Basic Auth with client ID/secret

### Frontend Components
- `OrderForm.js` - Main order creation interface
- `OrderValidation.jsx` - Order review and confirmation
- `ViewOrders.js` - Order history and management
- `UpdateInventory.js` - Stock level management
- `AddAddress.js`/`UpdateAddress.js` - Shipping address management

### Key Frontend Dependencies
- React 18.3.1 with React Router 6.27.0
- UI: Bootstrap 5.3.3, React Bootstrap 2.10.5
- Icons: lucide-react, react-icons
- File Upload: react-dropzone 14.3.5
- Testing: Jest with React Testing Library

### Backend Structure
- `main.py` - Core application logic, models, and API routes
- `config.py` - Flask configuration and database setup
- `app.py` - Application entry point for development
- `wsgi.py` - WSGI entry point for production
- `sendemail.py` - SendGrid email integration
- `shipstationcreate.py` - ShipStation order creation
- `shipping_label_creator.py` - Label generation utilities

## API Endpoints

All API endpoints are prefixed with `/api` and defined in `backend/main.py`:

### Shipping Addresses
- `POST /api/shipping-addresses` - Create new shipping address
- `GET /api/shipping-addresses` - List all shipping addresses
- `GET /api/shipping-addresses/<id>` - Get specific address
- `PUT /api/shipping-addresses/<id>` - Update address
- `DELETE /api/shipping-addresses/<id>` - Delete address

### Inventory Management
- `GET /api/inventory` - Get all inventory items with quantities
- `PUT /api/inventory/<sku>` - Update inventory quantity for specific SKU

### Orders
- `POST /api/orders` - Create new order (triggers ShipStation + SendGrid)
- `GET /api/orders` - Get all orders with details
- `GET /api/orders/<order_id>/attachment` - Download order attachment
- `POST /api/orders/<order_id>/void` - Void an order (restores inventory)

### Utilities
- `POST /api/process-labels` - Process shipping label PDFs

### Webhooks
- `POST /api/webhooks/shipping` - ShipStation webhook endpoint
- `POST /api/webhooks/shipstation` - Alternative ShipStation webhook

## Common Development Tasks

### Adding a New React Component
1. Create component file in `frontend/src/components/`
2. Import React and required hooks/libraries
3. Use Bootstrap components for UI consistency
4. Import in App.js and add to routing if needed

### Creating a New API Endpoint
1. Add route decorator in `backend/main.py`: `@app.route('/api/your-endpoint', methods=['GET', 'POST'])`
2. Implement function with proper error handling
3. Use `jsonify()` for responses
4. Test with frontend API_URL configuration

### Adding a Database Model
1. Define model class in `backend/main.py` inheriting from `db.Model`
2. Add necessary columns using `db.Column()`
3. Run `python init_db.py` to create tables
4. Use `db.session` for queries and transactions

## Development Best Practices

### CORS Configuration
- Backend automatically handles CORS for localhost:3000 (dev) and production domain
- Check `allowed_origins` in main.py if adding new frontend URLs

### Error Handling
- Backend: Always wrap in try/except, return JSON errors with appropriate HTTP codes
- Frontend: Check response.ok before processing data
- Use console.error() for debugging, show user-friendly messages

### Database Transactions
- Use `db.session.commit()` for changes
- Use `db.session.rollback()` in except blocks
- Use `db.session.flush()` to get IDs before final commit

### Code Organization
- Frontend: Keep components focused and reusable
- Backend: Keep routes thin, move complex logic to separate functions
- Use meaningful variable names matching the domain (e.g., `po` for purchase order)

### Testing
- Frontend tests: `cd frontend && npm test` - Runs Jest in watch mode
- Test files should follow `*.test.js` pattern
- Frontend uses React Testing Library for component testing

### Development Environment Notes
- SQLite database files (`*.db`) are gitignored for local development
- Python virtual environment should be created in `backend/venv/`
- Environment files follow `.env.*` pattern and are gitignored
- Frontend development server proxies API requests to backend (configured in package.json)