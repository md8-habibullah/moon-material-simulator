"""Target uses the optimizer designs for, with the properties each one needs.

`temps` are the temperatures (°C) the part must survive; every temperature-dependent requirement
is checked at each of them. Thresholds are engineering judgement for a first-pass screen, not
qualification criteria.
"""

APPLICATIONS = [
    {
        "id": "wrench",
        "label": "Wrench / hand tool",
        "icon": "wrench",
        "where": "Inside the habitat",
        "body": "any",
        "temps": [20],
        "summary": "Strong with a little give, so it bends before it shatters. NASA Glenn names wrenches as a target use.",
        "requirements": {
            "tensile_strength": {"min": 30},
            "elastic_modulus": {"min": 3},
            "elongation_at_break": {"min": 2},
            "max_service_temp": {"min": 60},
        },
    },
    {
        "id": "bracket",
        "label": "Structural bracket",
        "icon": "bracket",
        "where": "Inside the habitat",
        "body": "any",
        "temps": [20],
        "summary": "Stiff and strong in compression to hold shelves, cable trays and equipment.",
        "requirements": {
            "tensile_strength": {"min": 20},
            "compressive_strength": {"min": 45},
            "elastic_modulus": {"min": 4},
        },
    },
    {
        "id": "chair",
        "label": "Chair / furniture",
        "icon": "chair",
        "where": "Inside the habitat",
        "body": "any",
        "temps": [20],
        "summary": "Light enough to move around, tough enough to sit on every day.",
        "requirements": {
            "tensile_strength": {"min": 15},
            "elongation_at_break": {"min": 1.5},
            "density": {"max": 1.9},
        },
    },
    {
        "id": "lunar_panel",
        "label": "Outdoor wall panel (Moon)",
        "icon": "panel",
        "where": "Lunar surface, day and night",
        "body": "moon",
        "temps": [-173, 127],
        "summary": "Has to carry load from lunar night to lunar noon without softening in the sun.",
        "requirements": {
            "compressive_strength": {"min": 30},
            "elastic_modulus": {"min": 5},
            "max_service_temp": {"min": 127},
        },
    },
    {
        "id": "mars_block",
        "label": "Shelter block (Mars)",
        "icon": "block",
        "where": "Martian surface",
        "body": "mars",
        "temps": [-125, 20],
        "summary": "Dense, load-bearing blocks for a regolith-shielded shelter.",
        "requirements": {
            "compressive_strength": {"min": 35},
            "density": {"min": 1.8},
            "max_service_temp": {"min": 40},
        },
    },
    {
        "id": "nozzle",
        "label": "Thruster nozzle",
        "icon": "flame",
        "where": "Engine exhaust",
        "body": "any",
        "temps": [20],
        "summary": "Rocket exhaust runs well above 1,000 °C. We check honestly whether any mix can take it.",
        "requirements": {"max_service_temp": {"min": 1000}},
        "infeasible_note": (
            "No plastic composite survives exhaust temperatures: every binder here softens below "
            "about 350 °C. Nozzles need sintered regolith, ceramics or refractory metals. Use these "
            "bioplastic mixes for brackets, tools and interior parts instead."
        ),
    },
]
