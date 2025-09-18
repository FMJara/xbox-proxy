import express from "express";
import xboxGamesHandler from "./api/xbox-games.js";

const app = express();
const PORT = process.env.PORT || 3000;

// Endpoint igual que en Vercel
app.get("/api/xbox-games", (req, res) => xboxGamesHandler(req, res));

app.get("/", (req, res) => {
  res.json({
    message: "API de Juegos de Xbox 🎮",
    status: "activo",
    endpoints: {
      "/api/xbox-games": "Obtiene la lista de juegos de Xbox con caché",
    },
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor local corriendo en http://localhost:${PORT}`);
});
