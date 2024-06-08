# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OCRTimesheet(models.Model):

    _name = "ocr.timesheet"
    _description = "OCR Timesheet"
    _rec_name = "name"

    name = fields.Char("Name")
    badge_number = fields.Char("Badge Number")
    division = fields.Char("Division")
    cost_center = fields.Char("Cost Center")
