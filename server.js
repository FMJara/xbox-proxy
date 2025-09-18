import express from "express";
import axios from "axios";
import cors from "cors";
import NodeCache from "node-cache";
import schedule from "node-schedule";
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
const MAX_PAGES = 2; // Limitar el número de páginas a obtener inicialmente

/**
 * Función que usa paginación para obtener los primeros juegos de la API de Microsoft.
 */
async function fetchAllGames() {
  console.log("🔍 Iniciando la obtención de todos los juegos de la API de Microsoft...");
  let allProducts = [];
  let skip = 0;
  let totalItemsFound = 0;
  let pagesFetched = 0;

  try {
    while (pagesFetched < MAX_PAGES) { // Solo obtener un número limitado de páginas
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
      totalItemsFound = res.data.TotalItems || totalItemsFound;
      pagesFetched++;
      
      console.log(`Paginación: Obtenidos ${allProducts.length} juegos de ${totalItemsFound}.`);

      if (items.length < COUNT) {
          break;
      }
    }
    console.log(`✅ ¡Proceso de obtención de juegos completado! Total: ${allProducts.length}`);
    return allProducts;
  } catch (err) {
    console.error(`❌ Error al obtener juegos de la API de Microsoft: ${err.message}`);
    return allProducts;
  }
}

/**
 * Función que se ejecuta en un cron job para actualizar el caché.
 */
async function updateCache() {
  const games = await fetchAllGames();
  if (games.length > 0) {
    gameCache.set(CACHE_KEY, games);
    console.log(`📦 Caché actualizado con ${games.length} juegos.`);
  } else {
    console.log("⚠️ No se pudo obtener la lista de juegos para actualizar el caché.");
  }
}

// Iniciar el job de actualización al arrancar el servidor
updateCache();

// Programar la tarea para que se ejecute cada 12 horas
schedule.scheduleJob('0 */12 * * *', updateCache);

// Endpoints de la API
app.get("/xbox-games", (req, res) => {
  const games = gameCache.get(CACHE_KEY);
  
  if (!games) {
    return res.status(503).json({
      message: "El caché aún no se ha llenado. Por favor, inténtalo de nuevo en un momento.",
      status: "pendiente"
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
