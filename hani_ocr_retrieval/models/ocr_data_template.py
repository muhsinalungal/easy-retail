# -*- coding: utf-8 -*-

import io
import os
import pytesseract
import re
import spacy
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OCRDataTemplate(models.TransientModel):
    """Class to read document and extract the text from JPG, JPEG, PNG and
    PDF files."""

    _name = "ocr.data.template"
    _description = "Data Retrieving Template"
    _rec_name = "file_name"

    image = fields.Binary(
        string="Document", required=True, help="Upload .jpg, .jpeg, .png or .pdf files"
    )
    file_name = fields.Char(string="Document Name", help="Name of document")
    image2 = fields.Image(string="Document", help="Uploaded document", store=True)
    flag = fields.Boolean(
        string="Flag", default=False, help="Flag to check document read or not"
    )
    data = fields.Text(string="Data", help="Content from the document")
    model_name_id = fields.Many2one(
        "ir.model",
        string="Model",
        domain="[('model', 'in', ['ocr.timesheet'])]",
        help="Model to which the data want to map",
    )
    model_field_ids = fields.Many2many(
        "ir.model.fields",
        string="Fields",
        domain="[('model_id', '=', model_name_id)]",
        help="Fields names to map data",
    )

    def data_segmentation(self, img):
        """
        Function to do segmentation for the retrieved data after converting it
        into image
        """

        img = ImageOps.grayscale(img)
        threshold_value = 176
        img = img.point(lambda x: 255 if x > threshold_value else 0, "1")
        img_rgb = ImageOps.invert(img.convert("RGB"))
        segments = []
        segment_bounds = img_rgb.getbbox()
        while segment_bounds:
            segment = img_rgb.crop(segment_bounds)
            if segment.size[0] > 0 and segment.size[1] > 0:
                segments.append(segment)
            img_rgb = ImageOps.crop(img_rgb, segment_bounds)
            segment_bounds = img_rgb.getbbox()
        return segments

    def action_get_data(self):
        """
        Function to get the files in .jpg, .jpeg, .png and .pdf formats
        """
        split_tup = os.path.splitext(self.file_name)
        try:
            # Getting the file path from ir.attachments
            file_attachment = self.env["ir.attachment"].search(
                [
                    "|",
                    ("res_field", "!=", False),
                    ("res_field", "=", False),
                    ("res_id", "=", self.id),
                    ("res_model", "=", "ocr.data.template"),
                ],
                limit=1,
            )
            file_path = file_attachment._full_path(file_attachment.store_fname)
            segmented_data = []
            # Reading files in the format .jpg, .jpeg and .png
            if (
                split_tup[1] == ".jpg"
                or split_tup[1] == ".jpeg"
                or split_tup[1] == ".png"
            ):
                with open(file_path, mode="rb") as f:
                    binary_data = f.read()
                img = Image.open(io.BytesIO(binary_data))
                # Calling the function to do segmentation
                segmented_data = self.data_segmentation(img)
            elif split_tup[1] == ".pdf":
                # Reading files in the format .pdf
                with open(file_path, mode="rb") as f:
                    pdf_data = f.read()
                pages = convert_from_bytes(pdf_data)
                # Making the contents in 2 or more pages into combined page
                max_width = max(page.width for page in pages)
                total_height = sum(page.height for page in pages)
                resized_images = []
                for page in pages:
                    resized_page = page.resize((2400, 1800))
                    resized_images.append(resized_page)
                combined_image = Image.new("RGB", (max_width, total_height))
                y_offset = 0
                for resized_page in resized_images:
                    combined_image.paste(resized_page, (0, y_offset))
                    y_offset += resized_page.height
                # Calling the segmentation function
                segmented_data = self.data_segmentation(combined_image)
        except Exception:
            self.env["ocr.data.template"].search([], order="id desc", limit=1).unlink()
            raise ValidationError(_("Cannot identify data"))
        # Converting the segmented image into text using pytesseract
        text = ""
        for segment in segmented_data:
            try:
                text += pytesseract.image_to_string(segment) + "\n"
                break
            except Exception:
                raise ValidationError(_("Data cannot be read"))
        # Assigning retrieved data into text field
        self.data = text
        self.flag = True

    @api.onchange("model_name_id")
    def onchange_model_name_id(self):
        """Function to update the Many2many field to empty"""
        self.write({"model_field_ids": [(6, 0, [])]})

    def find_person_name(self):
        """
        Function to find person name from the retrieved text using 'spacy'
        """
        person = ""
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(self.data)
        for entity in doc.ents:
            if entity.label_ == "PERSON":
                person = entity.text
                break
        return person

    def action_process_data(self):
        """
        Function to process the data after fetching it.
        The fetched data are mapping into some models.
        """
        badge_number = ""
        division = ""
        cost_center = ""
        person = ""
        phone_pattern = ""

        if self.model_name_id.name == "OCR Timesheet":
            # Mapping the data into OCR timesheet module by fetching person name,
            # badge number, cost center and division

            for line in self.data.splitlines():
                print(line)
                if 'Name' in line:
                    person = line[5:]
                if 'Badge No' in line:
                    badge_number = line[11:]

                if 'Division' in line:
                    break

            # Creating record in res.partner
            ocr_timesheet = self.env["ocr.timesheet"].create(
                    {"name": person,
                     "badge_number": badge_number,
                     "division": division,
                     "cost_center": cost_center
                     })

            if ocr_timesheet:
                return {
                    "name": "OCR Timesheet",
                    "type": "ir.actions.act_window",
                    "view_type": "form",
                    "view_mode": "form",
                    "res_model": "ocr.timesheet",
                    "res_id": ocr_timesheet.id,
                    "view_id": self.env.ref("hani_ocr_retrieval.ocr_timesheet_view_form").id,
                    "target": "current",
                }

    @api.onchange("image")
    def _onchange_image(self):
        self.write({"image2": self.image})
