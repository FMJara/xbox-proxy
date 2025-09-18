import axios from "axios";
import fs from "fs";

async function getPCGames() {
  try {
    // 1️⃣ Traer los IDs de Game Pass (limitamos a 50 para no saturar)
    const gamepassRes = await axios.get(
      "https://catalog.gamepass.com/sigls/v2",
      {
        params: {
          language: "es-ar",
          market: "AR",
          hydration: "MobileDetails",
        },
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept: "application/json",
        },
      }
    );

    const allIds = gamepassRes.data.map((item) => item.id).slice(0, 50);

    console.log(`🔹 Obtenidos ${allIds.length} IDs de Game Pass.`);

    if (allIds.length === 0) return;

    // 2️⃣ Consultar DisplayCatalog con esos IDs
    const displayRes = await axios.get(
      "https://displaycatalog.mp.microsoft.com/v7.0/products",
      {
        params: {
          bigIds: allIds.join(","),
          market: "AR",
          languages: "es-AR",
          "MS-CV": "DGU1mcuYo0WMMp+F.1",
        },
        headers: {
          "User-Agent": "Mozilla/5.0",
          Accept: "application/json",
        },
      }
    );

    const products = displayRes.data.Products;

    // 3️⃣ Filtrar solo juegos compatibles con PC
    const pcGames = products.filter((p) =>
      p.Availabilities.some((av) =>
        av.Conditions.ClientConditions.AllowedPlatforms.some(
          (plat) => plat.PlatformName === "Windows.Desktop"
        )
      )
    );

    console.log(`✅ Juegos compatibles con PC: ${pcGames.length}`);

    // 4️⃣ Mostrar título e ID
    pcGames.forEach((g) =>
      console.log(`- ${g.ProductTitle} (ID: ${g.ProductId})`)
    );

    // 5️⃣ Opcional: guardar en archivo JSON
    fs.writeFileSync("pc-games.json", JSON.stringify(pcGames, null, 2));
    console.log("📂 Guardado en pc-games.json");
  } catch (err) {
    console.error("❌ Error:", err.message);
  }
}

getPCGames();
