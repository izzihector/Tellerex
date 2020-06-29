from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp
from werkzeug.urls import url_encode
import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone, UTC
import calendar


class ticl_scrap_stock(models.Model):
    _inherit = 'stock.scrap'
    _description = "Scrap"
    # _order = 'delivery_date desc, id desc'

    ticl_scrap_cancel_reason = fields.Char(string='Cancel Scrap Reason')
