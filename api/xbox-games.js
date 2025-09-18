import axios from "axios";
import NodeCache from "node-cache";
import https from "https";

const CACHE_TTL = 60 * 60 * 24; // 24 horas
const CACHE_KEY = "xboxGames";
const gameCache = new NodeCache({ stdTTL: CACHE_TTL });

const httpsAgent = new https.Agent({ maxSockets: 5 });

const BASE_URL = "https://reco-public.rec.mp.microsoft.com/channels/Reco/V8.0/Lists/Computed/pc";
const MARKET = "AR";
const LANGUAGE = "es";
const COUNT = 100;
const MAX_PAGES = 3;

async function fetchGames() {
  let allProducts = [];
  let skip = 0;
  let pagesFetched = 0;

  try {
    while (pagesFetched < MAX_PAGES) {
      const res = await axios.get(BASE_URL, {
        params: {
          Market: MARKET,
          Language: LANGUAGE,
          ItemTypes: "Game",
          DeviceFamily: "Windows.Desktop",
          count: COUNT,
          skipitems: skip,
        },
        headers: { "User-Agent": "Mozilla/5.0" },
        httpsAgent,
        timeout: 30000,
      });

      const items = res.data.Items || [];
      if (items.length === 0) break;

      allProducts.push(
        ...items.map((p) => ({
          id: p.Id,
          name: p.Title || "Sin nombre",
          price: p.Price?.ListPrice?.toString() || "N/A",
          link: p.Uri || "#",
        }))
      );

      skip += COUNT;
      pagesFetched++;
    }

    if (allProducts.length > 0) {
      gameCache.set(CACHE_KEY, {
        data: allProducts,
        updatedAt: Date.now(),
      });
    }

    return allProducts;
  } catch (err) {
    console.error("❌ Error API:", err.message);
    return [];
  }
}

export default async function handler(req, res) {
  let cached = gameCache.get(CACHE_KEY);

  if (!cached) {
    const games = await fetchGames();
    if (games.length === 0) {
      return res.status(503).json({
        message: "No se pudieron obtener los juegos",
        status: "error",
      });
    }
    cached = gameCache.get(CACHE_KEY);
  }

  res.status(200).json({
    games: cached.data,
    total: cached.data.length,
    lastUpdated: new Date(cached.updatedAt).toISOString(),
    source: "datos-de-cache",
  });
}
