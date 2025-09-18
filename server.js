import express from "express";
import axios from "axios";
import cors from "cors";
import NodeCache from "node-cache";
import https from "https";

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;
const CACHE_TTL = 60 * 60 * 24; // Caché por 24 horas
const CACHE_KEY = "xboxGames";
const gameCache = new NodeCache({ stdTTL: CACHE_TTL });

// Creamos un agente HTTPS para manejar la conexión de forma robusta
const httpsAgent = new https.Agent({
  rejectUnauthorized: false,
  maxSockets: 5
});

// API de Microsoft para juegos de PC
const BASE_URL = "https://reco-public.rec.mp.microsoft.com/channels/Reco/V8.0/Lists/Computed/pc";
const MARKET = "AR";
const LANGUAGE = "es";
const COUNT = 100; // Juegos por página
const MAX_PAGES = 3; // Límite de páginas para la carga inicial

// Bandera para evitar múltiples llamadas de carga inicial
let isFetchingInitialData = false;

/**
 * Función que usa paginación para obtener los primeros juegos de la API de Microsoft.
 */
async function fetchAndCacheInitialGames() {
  if (isFetchingInitialData) {
    console.log("⚠️ Ya se está cargando la data inicial. Saliendo...");
    return;
  }
  isFetchingInitialData = true;

  console.log("🔍 Iniciando la obtención de los primeros juegos de la API de Microsoft...");
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
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept: "application/json",
        },
        timeout: 30000,
        httpsAgent: httpsAgent,
      });

      const items = res.data.Items || [];

      if (items.length === 0) {
        break;
      }

      const mapped = items.map((p) => ({
        id: p.Id,
        name: p.Title || "Sin nombre",
        price: p.Price?.ListPrice?.toString() || "N/A",
        link: p.Uri || '#'
      }));

      allProducts = allProducts.concat(mapped);
      skip += COUNT;
      pagesFetched++;
      
      console.log(`Paginación: Obtenidos ${allProducts.length} juegos.`);
    }

    if (allProducts.length > 0) {
      gameCache.set(CACHE_KEY, allProducts);
      console.log(`✅ ¡Proceso de obtención de juegos completado! Total: ${allProducts.length}`);
    } else {
      console.log("⚠️ No se pudo obtener la lista de juegos para actualizar el caché.");
    }
  } catch (err) {
    console.error(`❌ Error al obtener juegos de la API de Microsoft: ${err.message}`);
  } finally {
    isFetchingInitialData = false;
  }
}

// Endpoints de la API
app.get("/xbox-games", (req, res) => {
  const games = gameCache.get(CACHE_KEY);
  
  if (!games || games.length === 0) {
    // Si el caché está vacío, iniciamos la carga en segundo plano
    if (!isFetchingInitialData) {
      console.log("Caché vacío, iniciando carga de datos en segundo plano...");
      fetchAndCacheInitialGames();
    }
    return res.status(202).json({
      message: "Cargando los juegos. Por favor, inténtalo de nuevo en unos segundos.",
      status: "cargando"
    });
  }

  const lastUpdated = new Date(gameCache.getStats().v[CACHE_KEY].t).toISOString();
  
  res.json({
    games,
    total: games.length,
    lastUpdated,
    source: 'datos-de-cache'
  });
});

app.get("/", (req, res) => {
  res.json({
    message: "API de Juegos de Xbox 🎮",
    status: "activo",
    endpoints: {
      "/xbox-games": "Obtiene la lista de juegos de Xbox de la caché (con paginación)",
    }
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor corriendo en puerto ${PORT}`);
});
