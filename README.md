# Panel de Mercados

Web personal para seguir los mercados día a día: sectores y factores de EE. UU., temáticos, Europa, emergentes y macro. Se actualiza sola dos veces cada día laborable (tras el cierre europeo y tras el de Wall Street) con cierres de Yahoo Finance. No necesita API key ni servidor.

## Ponerla en marcha (unos 10 minutos, una sola vez)

1. Crea una cuenta gratuita en [github.com](https://github.com) si no tienes.
2. Arriba a la derecha, **+ → New repository**. Nombre: `panel-mercados`. Márcalo como **Public** (GitHub Pages gratis requiere repositorio público; la web solo la encuentra quien tenga el enlace). Pulsa **Create repository**.
3. En la página del repositorio vacío, pulsa **uploading an existing file** y arrastra **todo el contenido** de la carpeta descomprimida, incluida la carpeta `.github`. Pulsa **Commit changes**.
   - Si tu ordenador oculta `.github` (empieza por punto), en Mac pulsa `Cmd + Mayús + .` en el Finder para verla.
4. **Settings → Pages**. En *Build and deployment → Source*, elige **GitHub Actions**.
5. **Actions** → *Actualizar panel* → **Run workflow**. En 1-2 minutos estará en verde.
6. Tu web queda en `https://TU-USUARIO.github.io/panel-mercados/`. Guárdala en la pantalla de inicio del móvil (Safari: Compartir → Añadir a pantalla de inicio).

A partir de ahí se actualiza sola. Para forzar una actualización: **Actions → Actualizar panel → Run workflow**.

## Cambiar lo que sigues

Abre `generar.py` en GitHub (icono del lápiz) y edita la lista `UNIVERSO`. Cada línea es `("TICKER", "Nombre")`, con el ticker tal y como aparece en finance.yahoo.com:

- ETFs y acciones: `SMH`, `NVDA`
- Índices: `^GSPC`, `^IBEX`
- Europa: `.DE` (Xetra), `.MC` (Madrid), `.PA` (París), `.MI` (Milán), `.L` (Londres)
- Divisas `EURUSD=X`, futuros `GC=F`, cripto `BTC-USD`

`ref` es la referencia contra la que se calcula la fuerza relativa de cada bloque. Puedes añadir bloques nuevos copiando uno existente (por ejemplo, tu lista de seguimiento).

## Probarla en tu ordenador

```bash
pip install -r requirements.txt
python generar.py          # datos reales → web/index.html
python generar.py --demo   # datos inventados, para probar cambios de diseño
```

## Qué muestra

- **Resumen**: pulso de índices, divisas, materias primas y bonos; rotación de sectores en EE. UU. y Europa; los más fuertes y más débiles del periodo; amplitud (% por encima de las medias de 50 y 200 sesiones).
- **Cada bloque**: tabla de calor 1D / 1S / 1M / 3M / YTD / 1A, distancia a la media de 200, mapa de rotación frente a la referencia y ranking.
- **Ficha de cada activo**: precio con medias de 50 y 200, rentabilidades y fuerza relativa frente a su referencia.

Notas: los ETFs están ajustados por dividendos; los índices van en divisa local; los bonos se miden en puntos básicos. Yahoo Finance es una fuente gratuita no oficial: si algún ticker falla un día, la web se publica igualmente con el resto.
