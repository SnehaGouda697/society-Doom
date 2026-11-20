# Society Doom

Society Doom is a society management dashboard with an Angular frontend and a FastAPI GraphQL backend. It gives administrators an overview of community health and billing, and lets residents view their home report, bills, and utility usage.

## Features

- Role-based admin and resident sign-in
- Society health score, monthly billing, collection progress, revenue breakdown, and home rankings
- Property directory, tenant directory, and monthly finance ledger
- Resident maintenance requests with admin status updates
- Admin tools for monthly bill generation, meter readings, community points, and gym logs
- SQLite database created at `backend/society_doom.db`

## Requirements

- Python 3.10 or newer
- Node.js and npm

## Start the backend

Run these commands from the project root in PowerShell. Create and activate a virtual environment, then install the backend packages:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install fastapi "uvicorn[standard]" "strawberry-graphql[fastapi]" sqlalchemy "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==4.0.1"
```

Seed the demo accounts and sample society data, then start the API:

```powershell
python -m backend.seed
python -m uvicorn backend.main:app --reload --port 8000
```

Keep this terminal open while using the app. The API health check is at <http://localhost:8000/health>; the GraphQL endpoint is at <http://localhost:8000/graphql>.

The seed command only creates demo data when the database has no users. It can be run again safely; existing user data is left in place.

## Start the frontend

Open a second PowerShell terminal:

```powershell
cd frontend
npm install
npm start
```

Open <http://localhost:4200>. The Angular app sends GraphQL requests to `http://localhost:8000/graphql`.

To create a production frontend build, run this from the `frontend` directory:

```powershell
npm run build
```

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Administrator | `admin@doom.com` | `admin123` |
| Resident | `resident01@doom.com` through `resident20@doom.com` | `resident123` |

## Project layout

```text
backend/   FastAPI app, GraphQL schema, database models, and seed data
frontend/  Angular app and Society Doom dashboard
```


## Live demo

- App: https://society-doom.vercel.app
- API (GraphQL): https://society-doom-api.onrender.com/graphql
- API health check: https://society-doom-api.onrender.com/health

Admin login: `admin@doom.com` / `admin123`
Resident login: `resident01@doom.com` / `resident123`

The API runs on a free tier, so the first request may take about 50 seconds to wake up.
