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


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    mlfb = fields.Char(string='MLFB')
    sap_material_number = fields.Char(string='SAP Material Number')
    org_id_supplier = fields.Char(string='Org ID Supplier')
    vendor_number = fields.Char(string='Vendor Number')
    profit_center = fields.Char(string='Profit Center')
    depth_structure = fields.Char(string='Depth Structure')
    pck = fields.Char(string='Product Classification Key')
    gck = fields.Char(string='Group Classification Key')
    hq_pg = fields.Char(string='Head Quarter Product Group')
    rc_pg = fields.Char(string='Regional Country Product Group')
    rc_pg_description = fields.Text(string='Regional Country Product Group Description')
    coo = fields.Char(string='Country Of Origin')
    unit_ga = fields.Float(string='Unit GA')
    ga_currency = fields.Many2one('res.currency', string='GA Currency')
    min_qty = fields.Float('Minimum Order Qty')
    unit_l1 = fields.Float(string='Unit L1')
    l1_currency = fields.Many2one('res.currency', string='L1 Currency')
    l1_urrency = fields.Many2one('res.currency', string='L1 Currency')
    unit_l2 = fields.Float(string='Unit L2')
    l2_currency = fields.Many2one('res.currency', string='L2 Currency')
    discount_1 = fields.Float(string='L2 Discount Level-1')
    discount_2 = fields.Float(string='L2 Discount Level-2')
    discount_3 = fields.Float(string='L2 Discount Level-3')
    is_available_distributor = fields.Selection([('available','Available'),('not_available','Not Available')],compute='_compute_is_available_distributor',search='_is_available_search',string='Available in other distributors')

    def _is_available_search(self, operator, value):
        recs = self.search([]).filtered(
            lambda x: x.is_available_distributor == value)
        if recs:
            return [('id', 'in', [x.id for x in recs])]

    def _compute_is_available_distributor(self):
        for rec in self:
            product_qty = self.env['stock.quant'].sudo().search([('product_id','=',rec.product_variant_id.id)])
            if product_qty:
                rec.is_available_distributor = 'available'
            else:
                rec.is_available_distributor = 'not_available'




class ProductProduct(models.Model):
    _inherit = 'product.product'

    mlfb = fields.Char(related="product_tmpl_id.mlfb",
                       readonly=False, store=True)
    sap_material_number = fields.Char(related="product_tmpl_id.sap_material_number",
                                      readonly=False, store=True)
    org_id_supplier = fields.Char(related="product_tmpl_id.org_id_supplier",
                                  readonly=False, store=True)
    vendor_number = fields.Char(related="product_tmpl_id.vendor_number",
                                readonly=False, store=True)
    profit_center = fields.Char(related="product_tmpl_id.profit_center",
                                readonly=False, store=True)
    depth_structure = fields.Char(related="product_tmpl_id.depth_structure",
                                  readonly=False, store=True)
    pck = fields.Char(related="product_tmpl_id.pck",
                      readonly=False, store=True)
    gck = fields.Char(related="product_tmpl_id.gck",
                      readonly=False, store=True)
    hq_pg = fields.Char(related="product_tmpl_id.hq_pg",
                        readonly=False, store=True)
    rc_pg = fields.Char(related="product_tmpl_id.rc_pg",
                        readonly=False, store=True)
    rc_pg_description = fields.Text(related="product_tmpl_id.rc_pg_description",
                                    readonly=False, store=True)
    coo = fields.Char(related="product_tmpl_id.coo",
                      readonly=False, store=True)
    unit_ga = fields.Float(related="product_tmpl_id.unit_ga",
                           readonly=False, store=True)
    l1_urrency = fields.Many2one(related="product_tmpl_id.l1_urrency",
                                 readonly=False, store=True)
    unit_l2 = fields.Float(related="product_tmpl_id.unit_l2",
                           readonly=False, store=True)
    l2_currency = fields.Many2one(related="product_tmpl_id.l2_currency",
                                  readonly=False, store=True)
    discount_1 = fields.Float(related="product_tmpl_id.discount_1",
                              readonly=False, store=True)
    discount_2 = fields.Float(related="product_tmpl_id.discount_2",
                              readonly=False, store=True)
    discount_3 = fields.Float(related="product_tmpl_id.discount_3",
                              readonly=False, store=True)


