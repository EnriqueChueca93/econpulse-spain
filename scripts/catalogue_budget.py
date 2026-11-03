"""Spanish for the Budget explorer (Batch 33d): what econpulse/budget.py writes in words. The page's prose is in
templates/es/budget-explorer.html, and what static/budget.js and static/pge.js write is in their own Spanish
dictionaries. The names of functions, types of spending, taxes, spending policies, chapters and ministries are the
publishers' own Spanish names, kept in econpulse/budget.py by code (FUNCTIONS_ES and the rest), since one English
name can stand for two Spanish ones. "Budget explorer", "General government", "never" and "{names} and {last}" are
in the catalogue already. Read by scripts/write_catalogue.py; the keys are the English exactly as the code writes it.
"""

PAIRS: dict[str, str] = {}

# ---------------------------------------------------------------- the page's description (templates/budget-explorer.html)
PAIRS.update({
    "What Spain's public administrations spend and raise, by theme, since 1995: functions, types of spending and taxes.":
        "Lo que gastan e ingresan las Administraciones públicas españolas, por temas, desde 1995: funciones, tipos de "
        "gasto e impuestos.",
})

# ---------------------------------------------------------------- the administrations (budget.LEVELS, explorer_data)
PAIRS.update({
    "The State (central government)": "El Estado (Administración central)",
    "Central government": "Administración central",
    "The State and its agencies (Administración central), without the Social Security.":
        "El Estado y sus organismos (Administración central), sin la Seguridad Social.",
    "The Social Security": "La Seguridad Social",
    "Social Security": "Seguridad Social",
    "The Social Security funds: contributory pensions and other benefits, and the public employment service.":
        "Los fondos de la Seguridad Social: las pensiones contributivas y otras prestaciones, y el servicio público de "
        "empleo.",
    "All autonomous communities": "Todas las comunidades autónomas",
    "Autonomous communities": "Comunidades autónomas",
    "The 17 autonomous communities together (Administración regional): they run most of health, education and social "
    "services, largely paid for by transfers from the State under the regional financing system.":
        "Las 17 comunidades autónomas en conjunto (Administración regional): gestionan la mayor parte de la sanidad, la "
        "educación y los servicios sociales, que se pagan en buena medida con transferencias del Estado a través del "
        "sistema de financiación autonómica.",
    "All public administrations": "Todas las Administraciones públicas",
    "Central, regional and local government and the Social Security together, consolidated: flows between them cancel "
    "out.":
        "Las Administraciones central, autonómica y local y la Seguridad Social en conjunto, consolidadas: los flujos "
        "entre ellas se compensan.",
    "The regional administration of {name}: spending by function from 2012, revenue and spending by type from 2000, "
    "taxes one by one from 2012.":
        "La administración autonómica de {name}: gasto por funciones desde 2012, ingresos y gasto por tipo desde 2000 e "
        "impuestos uno a uno desde 2012.",
})

# ---------------------------------------------------------------- notes in the page's prose (budget.rolled_note, provisional_note)
PAIRS.update({
    "the {year} budget has stayed in force in {years}": "el presupuesto de {year} se ha mantenido en vigor en {years}",
    "the {year} budget stayed in force in {years}": "el presupuesto de {year} se mantuvo en vigor en {years}",
    "{year} for spending by function": "{year} en el gasto por funciones",
    "{year} for spending by type and revenue": "{year} en el gasto por tipo y los ingresos",
})
