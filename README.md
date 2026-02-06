# DanBeem Ombudsman Tools and Resource Lab

Professional landing page and tools for the DanBeem Ombudsman team. Includes dashboards, facility lookup, and chain analysis.

## Setup & Running

### 1. **Frontend (HTTP Server)**
Start the static file server:

```bash
# Windows (PowerShell)
python -m http.server 8000

# Or with Node
npx http-server -p 8000
```

Then open: **http://localhost:8000**

### 2. **Backend (CMS API Proxy)**
The Chain Snapshot tool requires a backend proxy to fetch CMS data without CORS issues.

Install dependencies:
```bash
npm install
```

Start the proxy server:
```bash
npm start
```

This runs on **http://localhost:3000** and proxies requests to CMS APIs.

### 3. **Access the Tool**

Once both servers are running:
- **Landing Page:** http://localhost:8000/index.html
- **Impact Dashboard:** http://localhost:8000/dashboards/impact-2024.html
  - Interactive charts
  - Download PPTX presentation
- **Chain Snapshot:** http://localhost:8000/tools/chain-snapshot.html
  - Search facilities by name/city/state
  - Enter CCN directly
  - View facility details
  - See recent deficiencies (F-tags)

## Architecture

- **Frontend:** Static HTML/CSS/JS (no build step)
- **Backend:** Express.js proxy (fetches CMS data server-side)
- **Theme:** Dark glass UI with cyan/purple gradients
- **APIs:** CMS Provider of Services, Enforcement & Inspections data

## Features

### Landing Page
- Professional hero section
- Navigation to tools and dashboards
- Test environment disclaimer

### Impact Dashboard (FFY 2023 vs 2024)
- KPI cards: Total cases, facilities, staffing, resolution rate
- Bar chart comparing case volumes
- Download presentation (PPTX export via PptxGenJS)

### Chain Snapshot Tool
- **Two search modes:**
  - Direct CCN lookup (10-digit facility code)
  - Search by name, city, or state
- **Facility Summary:** Name, address, phone, beds, type
- **Deficiencies:** Recent F-tags with violation descriptions
- **Ownership Signals:** Placeholder for chain affiliation (configurable)

## Frontend Styling

All styles defined in `Assets/shared.css`:
- Dark background (#07101a)
- Glass-morphism panels
- Responsive layout (mobile-first)
- Accessibility: focus states, color contrast, semantic HTML

## Backend API Endpoints

Proxy server provides:

- `GET /api/health` — Health check
- `GET /api/search-facility?name=...&city=...&state=...` — Search facilities
- `GET /api/facility/:ccn` — Fetch facility by CCN
- `GET /api/deficiencies/:ccn` — Fetch deficiencies for facility

**Example:**
```bash
curl http://localhost:3000/api/search-facility?name=Sunrise&state=IL
```

## Fallback Behavior

If the backend is not running or CMS APIs are unavailable, the frontend gracefully falls back to demo data. This allows the tool to remain functional for UI testing.

## Deployment

### GitHub Pages (Frontend only)
1. Enable Pages in repository settings
2. Site: https://dbeem123.github.io/DanBeem/

⚠️ **Note:** Chain Snapshot tool requires backend to run; demo data only without it.

### Production Deployment
- Deploy Node.js backend to Heroku, AWS Lambda, or your own server
- Update `API_BASE` in `tools/chain-snapshot.html` to production backend URL
- Frontend can remain on GitHub Pages

## File Structure

```
DanBeem/
├── index.html                 # Landing page
├── Assets/
│   ├── shared.css            # Theme & components
│   └── shared.js             # Common utilities
├── dashboards/
│   └── impact-2024.html      # Impact Dashboard
├── tools/
│   └── chain-snapshot.html   # Chain Snapshot Tool
├── server.js                  # Node.js CMS proxy backend
├── package.json              # Backend dependencies
└── README.md                 # This file
```

## Notes

- **No sensitive data stored** — all queries are on-demand
- **CORS-safe** — backend proxy prevents browser-level CORS errors
- **Lightweight** — minimal dependencies, fast load times
- **Test environment flag** — clear disclaimer on all pages

## Contact & Support

For issues or questions, refer to the repository issues or contact the DanBeem team.
