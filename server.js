// server.js
import express from "express";
import fetch from "node-fetch";

const app = express();
const PORT = process.env.PORT || 3000;

app.get("/", (req, res) => {
  res.send("✅ Proxy Xbox funcionando en Render!");
});

app.get("/xbox-games", async (req, res) => {
  try {
    const url = "https://www.xbox.com/es-AR/games/all-games/pc?PlayWith=PC";

    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        Accept: "text/html",
      },
    });

    const text = await response.text();

    const regex = /"productId":"(.*?)"/g;
    let match;
    const ids = [];
    while ((match = regex.exec(text)) !== null) {
      ids.push(match[1]);
    }

    res.json({ total: ids.length, productIds: ids });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor escuchando en puerto ${PORT}`);
});
