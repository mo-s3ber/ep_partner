# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MakeStockPicking(models.TransientModel):
    _name = "make.stock.picking"
    _description = "Make Stock Picking"

    distributor_id = fields.Many2one('res.users', string='Distributor')
    distributor_available = fields.Many2many('res.users', string='Distributors')
    item_ids = fields.One2many(
        comodel_name="make.stock.picking.item",
        inverse_name="wiz_id",
        string="Items",
    )

    @api.model
    def _prepare_item(self, line):
        return {
            "line_id": line.id,
            "inquiry_id": line.inquiry_id.id,
            "product_id": line.product_id.id,
            "product_qty": line.product_qty,
            "product_uom_id": line.product_id.uom_id.id,
            "scheduled_date": line.scheduled_date,
        }

    @api.model
    def get_items(self, request_line_ids):
        request_line_obj = self.env["purchase.inquiry.line"]
        items = []
        request_lines = request_line_obj.browse(request_line_ids)
        for line in request_lines.filtered(lambda x: not x.is_transferred):
            items.append([0, 0, self._prepare_item(line)])
        return items

    @api.model
    def get_distributor(self, request_line_ids):
        request_line_obj = self.env["purchase.inquiry.line"]
        items = []
        request_lines = request_line_obj.browse(request_line_ids)
        for line in request_lines.filtered(lambda x: not x.is_transferred):
            if line.distributor_id:
                items.append(line.distributor_id.id)
        return items

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model", False)
        request_line_ids = []
        if active_model == "purchase.inquiry.line":
            request_line_ids += self.env.context.get("active_ids", [])
        elif active_model == "purchase.inquiry":
            request_ids = self.env.context.get("active_ids", False)
            request_line_ids += (
                self.env[active_model].browse(request_ids).mapped("line_ids.id")
            )
        if not request_line_ids:
            return res
        res["item_ids"] = self.get_items(request_line_ids)
        res['distributor_available'] = self.get_distributor(request_line_ids)
        request_lines = self.env["purchase.inquiry.line"].browse(request_line_ids)
        distributor_ids = request_lines.mapped("distributor_id").ids
        if len(distributor_ids) == 1:
            res["distributor_id"] = distributor_ids[0]
        return res

    @api.model
    def _prepare_stock_picking(self, request_id, picking_type, company, origin):
        if not self.distributor_id:
            raise UserError(_("Enter a Distributor."))
        partner_id = self.distributor_id.partner_id
        data = {
            "request_id": request_id.id,
            "origin": origin,
            "partner_id": partner_id.id,
            "picking_type_id": picking_type.id,
            "location_id": partner_id.property_stock_supplier.id,
            "location_dest_id": picking_type.default_location_dest_id.id,
            "company_id": company.id,
        }
        return data

    @api.model
    def _prepare_picking_line(self, picking, item):
        if not item.product_id:
            raise UserError(_("Please select a product for all lines"))
        product = item.product_id

        # Keep the standard product UOM for purchase order so we should
        # convert the product quantity to this UOM
        qty = item.product_uom_id._compute_quantity(
            item.product_qty, product.uom_id or product.uom_id
        )
        # Suggest the supplier min qty as it's done in Odoo core
        date_deadline = item.scheduled_date
        location = False
        stock_quants = self.env['stock.quant'].sudo().search(
            [('product_id', '=', product.id),('available_quantity', '>=', qty), ('location_id', 'in', self.distributor_id.stock_location_ids.ids)])
        if stock_quants:
            location = stock_quants[0].location_id
        if not stock_quants:
            raise UserError(_("The required quantity is not available in the distributor's warehouse"))
        vals = {
            "picking_id": picking.id,
            "name": product.name,
            "product_id": product.id,
            "product_uom": product.uom_po_id.id or product.uom_id.id,
            "product_uom_qty": qty,
            "location_id": location.id,
            "location_dest_id": picking.location_dest_id.id,
            "date_deadline": date_deadline,
        }
        return vals

    def make_stock_picking(self):
        res = []
        picking_obj = self.env["stock.picking"]
        move_obj = self.env["stock.move"]
        request = self.item_ids[0].line_id.inquiry_id
        picking_data = self._prepare_stock_picking(
            request,
            request.picking_type_id,
            request.company_id,
            request.name,
        )
        picking = picking_obj.create(picking_data)
        for item in self.item_ids:
            line = item.line_id
            if line.distributor_id == self.distributor_id:
                # line.is_transferred = True
                if item.product_qty <= 0.0:
                    raise UserError(_("Enter a positive quantity."))
                picking_line_data = self._prepare_picking_line(picking, item)
                picking_line = move_obj.create(picking_line_data)
        res.append(picking.id)
        return {
            "domain": [("id", "in", res)],
            "name": _("Transfers"),
            "view_mode": "tree,form",
            "res_model": "stock.picking",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }


class MakeStockPickingItem(models.TransientModel):
    _name = "make.stock.picking.item"
    _description = "Make Stock Picking Item"

    wiz_id = fields.Many2one(
        comodel_name="make.stock.picking",
        string="Wizard",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    line_id = fields.Many2one(
        comodel_name="purchase.inquiry.line", string="Inquiry Request Line"
    )
    inquiry_id = fields.Many2one(
        comodel_name="purchase.inquiry",
        related="line_id.inquiry_id",
        string="Inquiry Request",
        readonly=False,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        related="line_id.product_id",
        readonly=False,
    )
    product_qty = fields.Float(
        string="Quantity", digits="Product Unit of Measure"
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="UoM"
    )
    scheduled_date = fields.Date('Scheduled Date')
