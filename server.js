import express from "express";
import axios from "axios";
import cors from "cors";
import NodeCache from "node-cache";

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;
const CACHE_TTL = 60 * 60; // 1 hora
const gameCache = new NodeCache({ stdTTL: CACHE_TTL });

const BASE_URL = "https://reco-public.rec.mp.microsoft.com/channels/Reco/V8.0/Lists/Computed/pc";
const MARKET = "US";       // Región
const LANGUAGE = "en";     // Idioma
const COUNT = 100;         // Juegos por página

async function fetchAllGames() {
  let allProducts = [];
  let skip = 0;
  let hasMore = true;

  while (hasMore) {
    try {
      console.log(`Fetching games: skip=${skip}, market=${MARKET}, url=${BASE_URL}`);
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
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
          Accept: "application/json",
          "Accept-Language": "en-US,en;q=0.9",
          "Referer": "https://www.microsoft.com/",
        },
        timeout: 15000, // 15s timeout
      });

      console.log(`Response status: ${res.status}`);
      console.log(`Raw response data:`, JSON.stringify(res.data, null, 2)); // Log completo
      const items = res.data.Items || [];
      console.log(`Items received: ${items.length}`);

      if (items.length === 0) {
        console.log(`No items returned at skip=${skip}. Stopping fetch.`);
        break;
      }

      const mapped = items.map((p) => ({
        id: p.Id,
        name: p.Title || "Sin nombre",
        price: p.Price?.ListPrice?.toString() || "N/A",
      }));

      allProducts = allProducts.concat(mapped);
      skip += COUNT;
      hasMore = items.length === COUNT;
    } catch (fetchErr) {
      console.error(`Error fetching games at skip=${skip}:`, fetchErr.message);
      console.error('Error details:', fetchErr.code, fetchErr.config?.url);
      if (fetchErr.code === 'ECONNREFUSED') {
        console.error('Connection refused - likely Render network restriction or Microsoft API block');
      }
      if (fetchErr.response) {
        console.error('API responded with:', fetchErr.response.status, fetchErr.response.data);
      }
      break;
    }
  }

  console.log(`Total juegos fetchados: ${allProducts.length}`);
  return allProducts;
}

app.get("/xbox-games", async (req, res) => {
  try {
    const products = await fetchAllGames();
    const cachedGames = gameCache.get("games");

    let newGames = [];
    let priceChanges = [];

    if (cachedGames) {
      newGames = products.filter(
        (p) => !cachedGames.some((cached) => cached.id === p.id)
      );
      priceChanges = products.filter((p) => {
        const cached = cachedGames.find((g) => g.id === p.id);
        return cached && cached.price !== p.price;
      });
      gameCache.set("games", products);
    } else {
      newGames = products;
      priceChanges = [];
      gameCache.set("games", products);
    }

    const total = products.length;
    console.log(`Respondiendo: ${total} total, ${newGames.length} nuevos, ${priceChanges.length} cambios`);

    res.json({ newGames, priceChanges, total });
  } catch (err) {
    console.error("Error en /xbox-games:", err.message);
    res.status(500).json({ error: err.message });
  }
});

app.get("/", (req, res) => {
  res.send("Servidor Xbox Proxy activo ✅");
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en puerto ${PORT}`);
});
