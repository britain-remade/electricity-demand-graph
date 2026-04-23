# BRM UK Electricity Demand Forecasts NationBuilder package

This package now uses the branded `brm_uk_electricity_demand_forecasts` chart as the source reference, rebuilt as a self-contained interactive HTML.

Files in this package:
- `chart-page-template.html`: paste this into the dedicated chart page `Template` tab.
- `embed-iframe-snippet.html`: paste this into the destination page `Template` tab after replacing `CHART_PAGE_URL`.
- `standalone-preview.html`: local preview copy of the chart page.

Admin steps:
1. Create a new `Basic` page for the chart only. Suggested slug: `brm-uk-electricity-demand-forecasts-chart`.
2. Open that page's `Template` tab. If NationBuilder asks, create a custom template first.
3. Turn on `Ignore layout template` so the chart page renders without the normal site header/footer.
4. Replace the template contents with `chart-page-template.html`, then save and publish.
5. Open the live chart page and copy its full URL.
6. Open the page where the chart should appear and paste `embed-iframe-snippet.html` into the `Template` tab.
7. Replace `CHART_PAGE_URL` with the live chart page URL and save.
8. Preview the page and adjust the iframe height if you want it taller or shorter.

Uploads required:
- None for the recommended route.

Notes:
- Hover or tap the chart to inspect yearly values.
- Keep the dedicated chart page out of navigation if it only exists to be embedded.
