# Xbox Proxy

Proxy para obtener productIds de juegos de PC en la Microsoft Store.

## Endpoints

- Test: `/` → "Proxy Xbox funcionando"
- Juegos: `/xbox-games` → JSON con total y array de productIds

## Deploy en Render

1. Crear nuevo Web Service en Render.
2. Subir ZIP de este proyecto.
3. Build: `npm install`
4. Start: `npm start`
5. Usar URL que Render asigna para la app DroidScript.
