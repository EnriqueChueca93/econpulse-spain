"""Spanish for the State's debt, security by security (Batch 34b): the block on the Fiscal and Financial pages.
Read by scripts/write_catalogue.py; the keys are the English exactly as econpulse/statedebt.py and pages.py write it.
"""

PAIRS: dict[str, str] = {}

PAIRS.update({
    "The State's debt, security by security": "La deuda del Estado, valor a valor",
    "What the State owes in Letras, Bonos and Obligaciones, as the Tesoro lists them: how much falls due each year, in principal and in coupons, and the interest rate each bond pays. A run-off view of today's debt: the State refinances most of what falls due with new issues, which are not in the bars. Inflation-linked bonds are at today's indexed amount.":
        "Lo que debe el Estado en Letras, Bonos y Obligaciones, según la relación del Tesoro: cuánto vence cada año, en "
        "principal y en cupones, y el tipo de interés que paga cada bono. Una vista de la deuda actual hasta su "
        "amortización: el Estado refinancia la mayor parte de lo que vence con nuevas emisiones, que no están en las "
        "barras. Los bonos indexados a la inflación figuran por su importe indexado actual.",
    # facts
    "Letras, Bonos and Obligaciones": "Letras, Bonos y Obligaciones",
    "outstanding; the Tesoro's list of {day}": "en circulación; relación del Tesoro a {day}",
    "Due in the next 12 months": "Vence en los próximos 12 meses",
    "of principal, and {coupons} of coupons": "de principal, y {coupons} de cupones",
    "Average coupon": "Cupón medio",
    "Bonos and Obligaciones, weighted by amount": "Bonos y Obligaciones, ponderado por importe",
    "Average life": "Vida media",
    "{years} years": "{years} años",
    "to maturity, weighted by amount": "hasta el vencimiento, ponderada por importe",
    "Data check": "Comprobación de los datos",
    "checked by AI": "verificado por IA",
    "on {day}, against {what}": "el {day}, frente a {what}",
    "the Tesoro's page": "la página del Tesoro",
    "read automatically from the Tesoro's web page; not yet compared with it by an AI":
        "leído automáticamente de la página web del Tesoro; una IA aún no lo ha cotejado con ella",
    # the repayments chart
    "The State's debt: what falls due each year": "La deuda del Estado: lo que vence cada año",
    "€ billion on the Letras, Bonos and Obligaciones outstanding on {day}; {year}: the rest of the year":
        "Miles de millones de € de las Letras, Bonos y Obligaciones en circulación el {day}; {year}: lo que queda de año",
    "Principal": "Principal",
    "Interest (coupons)": "Intereses (cupones)",
    "{source}; Macroscope calculation": "{source}; cálculo de Macroscope",
    "Tesoro Público": "Tesoro Público",
    # the bubble chart
    "The stock of debt by interest rate": "El saldo de deuda por tipo de interés",
    "Each bubble is a Bono or Obligación: its maturity, its coupon and, by its size, the amount outstanding; Letras pay no coupon":
        "Cada burbuja es un Bono u Obligación: su vencimiento, su cupón y, por su tamaño, el saldo vivo; las Letras no "
        "pagan cupón",
    "Maturity date": "Fecha de vencimiento",
    "Coupon": "Cupón",
    "Amount outstanding": "Saldo vivo",
    "Ordinary": "Ordinarios",
    "Inflation-linked": "Indexados a la inflación",
    "Green": "Verdes",
})
