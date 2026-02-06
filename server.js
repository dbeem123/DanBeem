// Simple Node.js backend proxy for CMS API
// Fetches facility data on-demand, no full dataset stored

const express = require('express');
const cors = require('cors');
const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// ===== API ROUTES =====

// Search facilities by name, city, state
app.get('/api/search-facility', async (req, res) => {
  try {
    const { name, city, state } = req.query;
    
    let filter = '';
    if (name) filter += `Facility%20Name%20contains%20'${encodeURIComponent(name)}'`;
    if (city) filter += (filter ? '%20AND%20' : '') + `City%20contains%20'${encodeURIComponent(city)}'`;
    if (state) filter += (filter ? '%20AND%20' : '') + `State%20=${encodeURIComponent(state)}`;

    const url = `https://data.cms.gov/api/views/homes/rows.json?filter=${filter}&limit=50`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error(`CMS API returned ${response.status}`);
    
    const data = await response.json();
    
    if (!data || data.length === 0) {
      return res.json([]);
    }

    const results = data.slice(0, 20).map(row => ({
      ccn: row[9] || 'UNKNOWN',
      name: row[1] || 'Unknown Facility',
      city: row[4] || 'Unknown',
      state: row[5] || 'Unknown'
    }));

    res.json(results);
  } catch (err) {
    console.error('Search error:', err.message);
    res.status(500).json({ error: 'Failed to search facilities', details: err.message });
  }
});

// Fetch single facility by CCN
app.get('/api/facility/:ccn', async (req, res) => {
  try {
    const { ccn } = req.params;
    
    const url = `https://data.cms.gov/api/views/homes/rows.json?filter=Provider%20ID%20=${encodeURIComponent(ccn)}&limit=1`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error(`CMS API returned ${response.status}`);
    
    const data = await response.json();
    
    if (!data || data.length === 0) {
      return res.status(404).json({ error: 'Facility not found' });
    }

    const row = data[0];
    const facility = {
      ccn: row[9] || ccn,
      name: row[1] || 'Unknown',
      city: row[4] || 'Unknown',
      state: row[5] || 'Unknown',
      address: `${row[4] || ''}, ${row[5] || ''} ${row[7] || ''}`.trim(),
      phone: row[8] || 'N/A',
      beds: row[10] || 'N/A',
      type: 'Skilled Nursing Facility'
    };

    res.json(facility);
  } catch (err) {
    console.error('Facility fetch error:', err.message);
    res.status(500).json({ error: 'Failed to fetch facility', details: err.message });
  }
});

// Fetch deficiencies for a facility
app.get('/api/deficiencies/:ccn', async (req, res) => {
  try {
    const { ccn } = req.params;
    
    const url = `https://data.cms.gov/api/views/wvyx-sxba/rows.json?filter=Provider%20ID%20=${encodeURIComponent(ccn)}&limit=20`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error(`CMS API returned ${response.status}`);
    
    const data = await response.json();
    
    if (!data || data.length === 0) {
      return res.json([]);
    }

    const deficiencies = data.map(row => ({
      ftag: row[5] || 'N/A',
      description: row[4] || 'Deficiency noted',
      date: row[7] ? new Date(row[7]).toLocaleDateString() : 'N/A'
    }));

    res.json(deficiencies);
  } catch (err) {
    console.error('Deficiency fetch error:', err.message);
    res.status(500).json({ error: 'Failed to fetch deficiencies', details: err.message });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'CMS proxy backend running' });
});

// ===== START SERVER =====
app.listen(PORT, () => {
  console.log(`✅ DanBeem CMS Proxy running on http://localhost:${PORT}`);
  console.log(`   Health check: http://localhost:${PORT}/api/health`);
  console.log(`   Frontend should call: http://localhost:${PORT}/api/...`);
});
