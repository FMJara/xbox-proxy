import express from "express";
import axios from "axios";
import cors from "cors";
import NodeCache from "node-cache";

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;
const CACHE_TTL = 60 * 60; // 1 hora
const gameCache = new NodeCache({ stdTTL: CACHE_TTL });

// Configuración de la API de Microsoft
const BASE_URL = "https://displaycatalog.mp.microsoft.com/v7.0/products";
const MARKET = "es-AR";
const PAGE_SIZE = 50; // Número de productos por página

async function fetchAllGames() {
  let allProducts = [];
  let start = 0;
  let hasMore = true;

  while (hasMore) {
    const res = await axios.get(BASE_URL, {
      params: {
        category: "Games",
        market: MARKET,
        locale: MARKET,       // <-- Agregado
        start: start,
        top: PAGE_SIZE,
      },
      headers: {
        "User-Agent": "Mozilla/5.0",
        Accept: "application/json",
      },
    });

    const products = res.data.Products || [];

    // Filtrar solo juegos compatibles con PC
    const pcGames = products.filter(
      (p) => p.Platforms && p.Platforms.includes("Windows.Desktop")
    );

    allProducts = allProducts.concat(
      pcGames.map((p) => ({
        id: p.ProductId,
        name: p.LocalizedProperties?.[0]?.ProductTitle || "Sin nombre",
        price:
          p.DisplaySkuAvailabilities?.[0]?.Sku?.ListPrice?.toString() || "N/A",
      }))
    );

    start += PAGE_SIZE;
    hasMore = products.length === PAGE_SIZE;
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

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});
