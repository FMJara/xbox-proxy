import express from "express";
import axios from "axios";
import cors from "cors";
import NodeCache from "node-cache";
import * as cheerio from "cheerio";

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3000;
const CACHE_TTL = 60 * 60;
const gameCache = new NodeCache({ stdTTL: CACHE_TTL });

// URL de Xbox
const XBOX_URL = "https://www.xbox.com/es-AR/games/all-games/pc?PlayWith=PC";

async function fetchXboxGames() {
  try {
    console.log("🔍 Iniciando scraping de Xbox...");
    
    const response = await axios.get(XBOX_URL, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br'
      },
      timeout: 15000
    });

    const $ = cheerio.load(response.data);
    const games = [];
    
    console.log("📄 Página cargada, buscando juegos...");

    // Estrategia 1: Buscar por estructura de tarjetas de juego
    $('[class*="game"], [class*="card"], [class*="item"]').each((index, element) => {
      try {
        const $el = $(element);
        const title = $el.find('h3, h2, [class*="title"], [class*="name"]').first().text().trim();
        const price = $el.find('[class*="price"], [class*="cost"], [class*="value"]').first().text().trim() || 'Gratis';
        let link = $el.find('a').attr('href') || $el.attr('href');
        
        if (title && title.length > 2 && !title.match(/^\d+$/) && !title.includes('©')) {
          if (link && !link.startsWith('http')) {
            link = `https://www.xbox.com${link}`;
          }
          
          const game = {
            id: `game-${index}-${Date.now()}`,
            name: title,
            price: price.replace(/\s+/g, ' ').substring(0, 50),
            link: link || '#'
          };
          
          // Evitar duplicados
          if (!games.some(g => g.name === game.name)) {
            games.push(game);
          }
        }
      } catch (error) {
        // Continuar con el siguiente elemento
      }
    });

    // Estrategia 2: Si no encontramos juegos, buscar por patrones más generales
    if (games.length === 0) {
      $('a').each((index, element) => {
        try {
          const $el = $(element);
          const href = $el.attr('href');
          const text = $el.text().trim();
          
          if (href && href.includes('/games/') && text.length > 3) {
            const game = {
              id: `fallback-${index}-${Date.now()}`,
              name: text,
              price: 'Precio no disponible',
              link: href.startsWith('http') ? href : `https://www.xbox.com${href}`
            };
            
            if (!games.some(g => g.name === game.name)) {
              games.push(game);
            }
          }
        } catch (error) {
          // Continuar
        }
      });
    }

    console.log(`✅ Encontrados ${games.length} juegos`);
    return games;

  } catch (error) {
    console.error('❌ Error en scraping:', error.message);
    
    // Fallback a la API de Microsoft
    try {
      console.log('🔄 Usando API de Microsoft como fallback...');
      return await fetchMicrosoftAPI();
    } catch (fallbackError) {
      console.error('❌ Fallback también falló:', fallbackError.message);
      return [];
    }
  }
}

// API de Microsoft como fallback
async function fetchMicrosoftAPI() {
  try {
    const BASE_URL = "https://reco-public.rec.mp.microsoft.com/channels/Reco/V8.0/Lists/Computed/pc";
    
    const response = await axios.get(BASE_URL, {
      params: {
        Market: "AR",
        Language: "es",
        ItemTypes: "Game",
        DeviceFamily: "Windows.Desktop",
        count: 50,
        skipitems: 0,
      },
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
      },
      timeout: 10000
    });

    const items = response.data.Items || [];
    return items.map((item, index) => ({
      id: item.Id || `ms-${index}-${Date.now()}`,
      name: item.Title || "Juego sin nombre",
      price: item.Price?.ListPrice?.toString() || "N/A",
      link: "#"
    }));

  } catch (error) {
    console.error('Error en API Microsoft:', error.message);
    return [];
  }
}

app.get("/xbox-games", async (req, res) => {
  try {
    console.log("📦 Obteniendo datos de juegos...");
    
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
          id: game.id,
          name: game.name,
          oldPrice: cached?.price,
          newPrice: game.price,
          link: game.link
        };
      });

      console.log(`🆕 Nuevos juegos: ${newGames.length}, 💰 Cambios de precio: ${priceChanges.length}`);
    } else {
      newGames = currentGames;
      console.log('Primera ejecución, todos los juegos se consideran nuevos');
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
    console.error("Error en servidor:", err);
    
    // Intentar devolver datos del cache si hay error
    const cachedGames = gameCache.get("games") || [];
    res.json({
      newGames: [],
      priceChanges: [],
      total: cachedGames.length,
      lastUpdated: new Date().toISOString(),
      source: 'cache-fallback',
      error: err.message
    });
  }
});

// Ruta simple para test
app.get("/test", async (req, res) => {
  try {
    const games = await fetchXboxGames();
    res.json({
      message: "Test exitoso",
      totalGames: games.length,
      sample: games.slice(0, 5)
    });
  } catch (error) {
    res.json({ error: error.message });
  }
});

// Ruta para limpiar cache
app.get("/clear-cache", (req, res) => {
  gameCache.flushAll();
  res.json({ message: "Cache limpiado" });
});

app.get("/", (req, res) => {
  res.json({
    message: "Xbox Games API 🎮",
    endpoints: {
      "/xbox-games": "Juegos nuevos y cambios de precio",
      "/test": "Test de scraping",
      "/clear-cache": "Limpiar cache"
    },
    status: "active"
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor corriendo en puerto ${PORT}`);
  console.log(`🌐 URL: http://localhost:${PORT}`);
});
