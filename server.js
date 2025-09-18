import express from "express";
import axios from "axios";
import cors from "cors";
import NodeCache from "node-cache";
import schedule from "node-schedule";
import { HttpsProxyAgent } from "https-proxy-agent";

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;
const CACHE_TTL = 60 * 60 * 24; // Cache for 24 hours
const CACHE_KEY = "xboxGames";
const gameCache = new NodeCache({ stdTTL: CACHE_TTL });

// URL de un proxy público para enmascarar la conexión y evitar bloqueos.
// Esto soluciona el problema de enrutamiento en el servidor de Render.
const PROXY_URL = 'http://165.22.186.208:8080';
const agent = new HttpsProxyAgent(PROXY_URL);

// API de Microsoft para juegos de PC
const BASE_URL = "https://reco-public.rec.mp.microsoft.com/channels/Reco/V8.0/Lists/Computed/pc";
const MARKET = "AR";
const LANGUAGE = "es";
const COUNT = 100; // Games per page

/**
 * Function that uses pagination to get all games from the Microsoft API.
 */
async function fetchAllGames() {
  console.log("🔍 Starting to fetch all games from the Microsoft API...");
  let allProducts = [];
  let skip = 0;
  let totalItemsFound = 0;

  try {
    while (true) {
      const res = await axios.get(BASE_URL, {
        params: {
          Market: MARKET,
          Language: LANGUAGE,
          ItemTypes: "Game",
          DeviceFamily: "Windows.Desktop",
          count: COUNT,
          skipitems: skip,
        },
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept: "application/json",
        },
        timeout: 60000,
        httpsAgent: agent, // Use the proxy agent
      });

      const items = res.data.Items || [];
      if (items.length === 0) {
        break;
      }

      const mapped = items.map((p) => ({
        id: p.Id,
        name: p.Title || "No Name",
        price: p.Price?.ListPrice?.toString() || "N/A",
        link: p.Uri || '#'
      }));

      allProducts = allProducts.concat(mapped);
      skip += COUNT;
      totalItemsFound = res.data.TotalItems || totalItemsFound;
      
      console.log(`Pagination: Fetched ${allProducts.length} games out of ${totalItemsFound}.`);

      if (items.length < COUNT) {
          break;
      }
    }
    console.log(`✅ Game fetching process completed! Total: ${allProducts.length}`);
    return allProducts;
  } catch (err) {
    console.error(`❌ Error fetching games from the Microsoft API: ${err.message}`);
    return allProducts;
  }
}

/**
 * Function that runs in a cron job to update the cache.
 */
async function updateCache() {
  const games = await fetchAllGames();
  if (games.length > 0) {
    gameCache.set(CACHE_KEY, games);
    console.log(`📦 Cache updated with ${games.length} games.`);
  } else {
    console.log("⚠️ Could not get the game list to update the cache.");
  }
}

// Start the cache update job on server startup
updateCache();

// Schedule the task to run every 12 hours
schedule.scheduleJob('0 */12 * * *', updateCache);

// API endpoints
app.get("/xbox-games", (req, res) => {
  const games = gameCache.get(CACHE_KEY);
  
  if (!games) {
    return res.status(503).json({
      message: "The cache is not yet populated. Please try again in a moment.",
      status: "pending"
    });
  }

  const lastUpdated = new Date(gameCache.getStats().v[CACHE_KEY].t).toISOString();
  
  res.json({
    games,
    total: games.length,
    lastUpdated,
    source: 'cached-data'
  });
});

app.get("/", (req, res) => {
  res.json({
    message: "Xbox Games API 🎮",
    status: "active",
    endpoints: {
      "/xbox-games": "Gets the list of Xbox games from the cache (with pagination)",
    }
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
});
