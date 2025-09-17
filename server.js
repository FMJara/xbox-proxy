import express from "express";
import axios from "axios";
import cors from "cors";
import NodeCache from "node-cache";

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;
const CACHE_TTL = 60 * 60; // 1 hora
const gameCache = new NodeCache({ stdTTL: CACHE_TTL });

// API de Microsoft para juegos de PC
const BASE_URL =
  "https://reco-public.rec.mp.microsoft.com/channels/Reco/V8.0/Lists/Computed/pc";
const MARKET = "AR";       // Región
const LANGUAGE = "es";     // Idioma
const COUNT = 100;         // Juegos por página

async function fetchAllGames() {
  let allProducts = [];
  let skip = 0;
  let hasMore = true;

  while (hasMore) {
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
    });

    const items = res.data.Items || [];
    if (items.length === 0) break;

    // Mapeo de datos
    const mapped = items.map((p) => ({
      id: p.Id,
      name: p.Title || "Sin nombre",
      price: p.Price?.ListPrice?.toString() || "N/A",
    }));

    allProducts = allProducts.concat(mapped);
    skip += COUNT;
    hasMore = items.length === COUNT;
  }

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

    res.json({ newGames, priceChanges, total });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

// Ruta raíz para verificar que el server anda
app.get("/", (req, res) => {
  res.send("Servidor Xbox Proxy activo ✅");
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});
