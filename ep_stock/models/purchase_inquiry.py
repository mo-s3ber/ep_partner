from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang


class PurchaseInquiry(models.Model):
    _name = 'purchase.inquiry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Inquiry Request'

    @api.model
    def _default_picking_type(self):
        type_obj = self.env["stock.picking.type"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        types = type_obj.search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id)]
        )
        if not types:
            types = type_obj.search(
                [("code", "=", "incoming"), ("warehouse_id", "=", False)]
            )
        return types[:1]

    name = fields.Char()
    date = fields.Datetime('Request Date', default=datetime.now())
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    note = fields.Text('Note')
    line_ids = fields.One2many('purchase.inquiry.line', 'inquiry_id', string='Inquiry Lines')
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Picking Type",
        required=True,
        default=_default_picking_type,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'), ('done', 'Done')
    ], string='Status', copy=False, index=True, readonly=True, default='draft')
    picking_count = fields.Integer(compute='_compute_picking_count')
    is_transferred = fields.Boolean(compute='_compute_is_transferred')


    @api.depends('line_ids')
    def _compute_is_transferred(self):
        for record in self:
            if all(c == True for c in record.line_ids.mapped('is_transferred')):
                record.is_transferred = True
            else:
                record.is_transferred = False

    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = self.env['stock.picking'].search_count([('request_id','=',rec.id)])

    def confirm(self):
        for rec in self:
            for line in rec.line_ids:
                line._compute_distributor_available()
        self.write({'state': 'confirm'})

    def done(self):
        self.write({'state': 'done'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('purchase.inquiry') or '/'
        return super(PurchaseInquiry, self).create(vals)

    def action_view_picking(self):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree_all").sudo().read()[0]
        action["domain"] = [("request_id", "=", self.id)]
        return action


class PurchaseInquiryLine(models.Model):
    _name = "purchase.inquiry.line"

    name = fields.Char('Description')
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade', required=True)
    order_qty = fields.Float('Order Quantity')
    qty_available = fields.Float(related='product_id.qty_available')
    distributor_id = fields.Many2one('res.users', string='Distributor')
    partner_id = fields.Many2one('res.partner', related='distributor_id.partner_id')
    product_qty = fields.Float('Confirmed Quantity')
    price_unit = fields.Float('Unit Price')
    scheduled_date = fields.Date('Scheduled Date')
    inquiry_id = fields.Many2one('purchase.inquiry')
    inquiry_state = fields.Selection(related='inquiry_id.state', store=True)
    distributor_available = fields.Many2many('res.users', string='Distributors')
    is_transferred = fields.Boolean()


    @api.constrains('product_qty')
    def _validate_product_qty(self):
        for rec in self:
            if rec.product_qty > 0.0 and rec.product_id and rec.distributor_id:
                stock_quants = self.env['stock.quant'].sudo().search([('product_id', '=', rec.product_id.id),('location_id', 'in', rec.distributor_id.stock_location_ids.ids)])
                available_quantity = sum(stock_quants.mapped('available_quantity'))
                if available_quantity < rec.product_qty:
                    raise ValidationError(_('You cannot confirm more than the existing quantity'))

    def _compute_distributor_available(self):
        for rec in self:
            distributors = []
            if rec.product_id:
                quants = self.env['stock.quant'].sudo().search([('product_id', '=', rec.product_id.id)])
                for quant in quants:
                    for user in quant.location_id.user_ids:
                        if user != rec.inquiry_id.user_id:
                            distributors.append(user.id)
            rec.distributor_available = distributors

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.standard_price
