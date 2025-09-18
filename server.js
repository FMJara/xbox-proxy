import express from "express";
import axios from "axios";
import cors from "cors";
import NodeCache from "node-cache";
import * as cheerio from "cheerio";

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;
const CACHE_TTL = 60 * 60; // 1 hora
const gameCache = new NodeCache({ stdTTL: CACHE_TTL });

// URL real de Xbox para scraping
const XBOX_URL = "https://www.xbox.com/es-AR/games/all-games/pc?PlayWith=PC";

async function fetchXboxGames() {
  try {
    console.log("🔍 Iniciando scraping de Xbox...");
    
    const response = await axios.get(XBOX_URL, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.9'
      },
      timeout: 10000
    });

    const $ = cheerio.load(response.data);
    const games = [];

    // Selectores REALES para la página de Xbox
    $('a[href*="/games/"]').each((index, element) => {
      try {
        const $el = $(element);
        const title = $el.find('h3, .text-title, .c-subheading-6').first().text().trim();
        const priceElement = $el.find('.price, .text-price, .font-weight-bold, [data-bind*="price"]').first();
        const price = priceElement.text().trim() || 'Gratis';
        const link = $el.attr('href');

        // Filtramos solo juegos válidos
        if (title && title.length > 3 && !title.includes('©') && !title.includes('®')) {
          const game = {
            id: `xbox-${index}-${Date.now()}`,
            name: title,
            price: price.replace(/\s+/g, ' '), // Limpia espacios extras
            link: link.startsWith('http') ? link : `https://www.xbox.com${link}`
          };

          // Evitar duplicados
          const exists = games.some(g => g.name === game.name);
          if (!exists) {
            games.push(game);
          }
        }
      } catch (error) {
        console.log('Error parsing game element:', error);
      }
    });

    console.log(`✅ Found ${games.length} games on Xbox page`);
    return games;

  } catch (error) {
    console.error('❌ Error scraping Xbox:', error.message);
    
    // Fallback a la API de Microsoft si el scraping falla
    try {
      console.log('🔄 Trying Microsoft API as fallback...');
      const fallbackGames = await fetchMicrosoftAPI();
      return fallbackGames;
    } catch (fallbackError) {
      console.error('❌ Fallback also failed:', fallbackError.message);
      return [];
    }
  }
}

// Tu función original de Microsoft API (como fallback)
async function fetchMicrosoftAPI() {
  const BASE_URL = "https://reco-public.rec.mp.microsoft.com/channels/Reco/V8.0/Lists/Computed/pc";
  
  let allProducts = [];
  let skip = 0;
  let hasMore = true;

  while (hasMore && skip < 500) { // Límite para no hacer loops infinitos
    try {
      const res = await axios.get(BASE_URL, {
        params: {
          Market: "AR",
          Language: "es",
          ItemTypes: "Game",
          DeviceFamily: "Windows.Desktop",
          count: 100,
          skipitems: skip,
        },
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept: "application/json",
        },
        timeout: 8000
      });

      const items = res.data.Items || [];
      if (items.length === 0) break;

      const mapped = items.map((p) => ({
        id: p.Id || `ms-${skip}-${Date.now()}`,
        name: p.Title || "Sin nombre",
        price: p.Price?.ListPrice?.toString() || "N/A",
      }));

      allProducts = allProducts.concat(mapped);
      skip += 100;
      hasMore = items.length === 100;

    } catch (error) {
      console.error('Error in Microsoft API:', error.message);
      break;
    }
  }

  return allProducts;
}

app.get("/xbox-games", async (req, res) => {
  try {
    console.log("📦 Fetching games data...");
    
    const currentGames = await fetchXboxGames();
    const cachedGames = gameCache.get("games") || [];

    let newGames = [];
    let priceChanges = [];

    if (cachedGames.length > 0) {
      // Detectar juegos nuevos
      newGames = currentGames.filter(
        current => !cachedGames.some(cached => cached.name === current.name)
      );

      // Detectar cambios de precio
      priceChanges = currentGames.filter(current => {
        const cachedGame = cachedGames.find(cached => cached.name === current.name);
        return cachedGame && cachedGame.price !== current.price;
      }).map(game => {
        const cached = cachedGames.find(cached => cached.name === game.name);
        return {
          ...game,
          oldPrice: cached?.price,
          newPrice: game.price
        };
      });

      console.log(`🆕 New games: ${newGames.length}, 💰 Price changes: ${priceChanges.length}`);
    } else {
      newGames = currentGames;
      console.log('First run, all games are considered "new"');
    }

    // Actualizar cache
    gameCache.set("games", currentGames);

    res.json({
      newGames,
      priceChanges,
      total: currentGames.length,
      lastUpdated: new Date().toISOString(),
      source: 'xbox-scraping'
    });

  } catch (err) {
    console.error("Server error:", err);
    res.status(500).json({ 
      error: err.message,
      fallback: "Using cached data if available"
    });
  }
});

// Ruta adicional para solo nuevos juegos
app.get("/new-games", async (req, res) => {
  try {
    const currentGames = await fetchXboxGames();
    const cachedGames = gameCache.get("games") || [];
    
    const newGames = currentGames.filter(
      current => !cachedGames.some(cached => cached.name === current.name)
    );

    res.json({
      newGames,
      totalNew: newGames.length,
      lastUpdated: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Ruta para forzar actualización
app.get("/refresh", async (req, res) => {
  gameCache.del("games"); // Limpiar cache
  const result = await fetchXboxGames();
  res.json({
    message: "Cache cleared and refreshed",
    totalGames: result.length,
    lastUpdated: new Date().toISOString()
  });
});

// Ruta raíz
app.get("/", (req, res) => {
  res.json({
    message: "Xbox Games Proxy Server ✅",
    endpoints: {
      "/xbox-games": "Main endpoint (new games + price changes)",
      "/new-games": "Only new games",
      "/refresh": "Force cache refresh"
    }
  });
});

app.listen(PORT, () => {
  console.log(`🎮 Servidor Xbox Proxy activo en http://localhost:${PORT}`);
  console.log(`⏰ Cache TTL: ${CACHE_TTL} segundos`);
});
