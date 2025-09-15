import express from "express";
import fetch from "node-fetch";
import cors from "cors";

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;

// Endpoint de Xbox Store para "All PC Games"
const BASE_URL =
  "https://storeedgefd.dsx.mp.microsoft.com/v8.0/pages/7f2c510b-6d4a-4b87-a0e8-6198f2b24e9e?market=AR&languages=es-AR";

// Función para obtener todos los juegos paginados
async function fetchAllGames() {
  let allProducts = [];
  let continuationToken = null;

  do {
    const url = continuationToken
      ? `${BASE_URL}&continuationToken=${continuationToken}`
      : BASE_URL;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const products = data?.Results?.Products || [];
    const mapped = products.map((p) => ({
      id: p.ProductId,
      name: p.LocalizedProperties[0]?.ProductTitle || "Sin nombre",
      price:
        p.DisplaySkuAvailabilities?.[0]?.Sku?.ListPrice?.toString() || "N/A",
    }));

    allProducts = allProducts.concat(mapped);
    continuationToken = data?.ContinuationToken || null;
  } while (continuationToken);

  return allProducts;
}

// Ruta del proxy
app.get("/xbox-games", async (req, res) => {
  try {
    const products = await fetchAllGames();
    res.json({ products });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});
