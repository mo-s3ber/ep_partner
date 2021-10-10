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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    internal_po_number = fields.Char('Internal PO Number',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    invoice_number = fields.Char('Invoice Number',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    icc_date = fields.Date('ICC Date',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    payment_condition = fields.Char('Payment Condition',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    oc_delivery_incoterm = fields.Char('OC Delivery Incoterm',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    oc_date = fields.Date('OC Date',states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)


