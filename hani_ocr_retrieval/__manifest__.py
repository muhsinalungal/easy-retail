# -*- coding: utf-8 -*-

{
    "name": "OCR Retrieval",
    "version": "1.0",
    "category": "Productivity",
    "summary": "Data retrieval from scanned documents",
    "description": """Data retrieval from scanned documents with .jpg,
     .jpeg, .png and .pdf files. Also mapping them to appropriate models""",
    "author": "Muhsin Kottakkuth",
    "company": "Muhsin Kottakkuth",
    "maintainer": "Muhsin Kottakkuth",
    "website": "https://www.linkedin.com/in/muhsinalungal/",
    "depends": ["base", "contacts"],

    "data": ["security/ir.model.access.csv",
             "views/ocr_data_template_views.xml",
             "views/ocr_timesheet.xml"],

    "external_dependencies": {
        "python": ["pdf2image", "PIL", "pytesseract", "spacy", "en_core_web_sm"]
    },
    "images": ["static/description/banner.jpg"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
