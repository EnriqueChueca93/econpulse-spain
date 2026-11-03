"""Spanish for the disclaimer (econpulse/disclaimer.py, the footer in templates/base.html and the RSS feed). Read by
scripts/write_catalogue.py; keys are the English exactly as written there. The About page's full terms are in
templates/es/about.html.
"""

PAIRS: dict[str, str] = {
    "For information only: not investment, financial or tax advice. Figures come from their sources and can be revised or contain errors, so check the source before relying on them. Macroscope Spain is independent and is not affiliated with or endorsed by any of them.":
        "Solo a título informativo: no es asesoramiento de inversión, financiero ni fiscal. Las cifras proceden de sus "
        "fuentes y pueden revisarse o contener errores, así que compruebe la fuente antes de basarse en ellas. "
        "Macroscope España es independiente y no está vinculado a ninguna de ellas ni cuenta con su respaldo.",
    "Disclaimer and terms of use": "Aviso legal y condiciones de uso",
    "Macroscope's text and charts:": "Textos y gráficos de Macroscope:",
    "Macroscope's own readings and estimates: calculations from public data with simple, documented methods, not official statistics, forecasts of record or investment advice. Forecasters' figures are theirs, as they published them.":
        "Lecturas y estimaciones propias de Macroscope: cálculos con datos públicos y métodos sencillos y documentados, "
        "no estadísticas oficiales, previsiones de referencia ni asesoramiento de inversión. Las cifras de los "
        "organismos de previsión son suyas, tal como las publicaron.",
    "Market prices, yields and rates as of the site's latest update, not live: for information only, not investment advice or a recommendation to buy or sell anything.":
        "Precios de mercado, rentabilidades y tipos a la fecha de la última actualización del sitio, no en tiempo real: "
        "solo a título informativo, no son asesoramiento de inversión ni una recomendación de comprar o vender nada.",
    "The tools run simple models on public data: their results show what the assumptions imply, and are not forecasts or advice.":
        "Las herramientas aplican modelos sencillos a datos públicos: sus resultados muestran lo que implican los "
        "supuestos, y no son previsiones ni asesoramiento.",
    "Macroscope Spain; text and charts under CC BY-NC 4.0; data under their sources' terms.":
        "Macroscope España; textos y gráficos bajo CC BY-NC 4.0; datos según las condiciones de sus fuentes.",
}
