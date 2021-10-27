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
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Purchase Inquiry Request'

    name = fields.Char()
    date = fields.Datetime('Request Date', default=datetime.now())
    user_id = fields.Many2one('res.users', string='Partner', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    note = fields.Text('Note')
    line_ids = fields.One2many('purchase.inquiry.line', 'inquiry_id', string='Inquiry Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'), ('done', 'Closed')
    ], string='Status', copy=False, index=True, readonly=True, default='draft')

    def confirm(self):
        self.write({'state': 'confirm'})

    def done(self):
        self.write({'state': 'done'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('purchase.inquiry') or '/'
        return super(PurchaseInquiry, self).create(vals)


class PurchaseInquiryLine(models.Model):
    _name = "purchase.inquiry.line"

    name = fields.Char('Description')
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade', required=True)
    order_qty = fields.Float('Order Quantity')
    qty_available = fields.Float(related='product_id.qty_available')
    partner_id = fields.Many2one('res.partner', string='Distributor')
    product_qty = fields.Float('Confirmed Quantity')
    price_unit = fields.Float('Unit Price')
    scheduled_date = fields.Date('Scheduled Date')
    inquiry_id = fields.Many2one('purchase.inquiry')
    inquiry_state = fields.Selection(related='inquiry_id.state',store=True)


    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.standard_price
