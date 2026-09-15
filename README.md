# Wijkwarm

Statische site op [wijkwarm.nl](https://wijkwarm.nl): gasverbruik, stroom, zonnepanelen, woningtype en ISDE-subsidie per wijk, voor alle Nederlandse gemeenten. Gehost via GitHub Pages vanaf `main`.

## Hoe het werkt

`pipeline/run.py` haalt de Kerncijfers wijken en buurten en de energietabel op bij het CBS (OData), bouwt per gemeente en per wijk een pagina en schrijft alles in de root van deze repository. De workflow in `.github/workflows/bijwerken.yml` draait dit op de derde van elke maand en bij elke wijziging in `pipeline/`, en commit het resultaat.

- `pipeline/config.json`: affiliate-links per maatregel en het AdSense-id. Leeg betekent geen knop en geen advertenties.
- `pipeline/subsidies.json`: ISDE-bedragen per jaar.
- `data/cbs.json`: de laatst opgehaalde CBS-data, zodat `python pipeline/run.py --rebuild` zonder netwerk werkt.

## Domein

1. Settings, Pages: bron `main`, map `/`, custom domain `wijkwarm.nl`, Enforce HTTPS aan. De workflow probeert dit ook zelf in te stellen.
2. DNS bij de registrar: `A`-records voor `wijkwarm.nl` naar `185.199.108.153`, `185.199.109.153`, `185.199.110.153` en `185.199.111.153`, en een `CNAME` voor `www` naar `gielklaas-speed40.github.io`.
