import pytz
from openerp import SUPERUSER_ID, workflow
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import attrgetter
from openerp.tools.safe_eval import safe_eval as eval
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record_list, browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.tools.float_utils import float_compare, float_is_zero


class purchase_order_line(osv.osv):
	_inherit = 'purchase.order.line'


	def _amount_line(self, cr, uid, ids, prop, arg, context=None):
		# print 'est======================33333333333'
		res = {}
		cur_obj=self.pool.get('res.currency')
		tax_obj = self.pool.get('account.tax')
		for line in self.browse(cr, uid, ids, context=context):
			line_price = self._calc_line_base_price(cr, uid, line,
													context=context)
			# print 'line_price====================', line_price
			if line_price == 0:
				line_price = line.expected_rate
			line_qty = self._calc_line_quantity(cr, uid, line,
												context=context)
			if line_qty == 0:
				line_qty = line.required_qty
			# print 'line_qty====================', line_qty
			taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line_price,
										line_qty, line.product_id,
										line.order_id.partner_id)
			cur = line.order_id.pricelist_id.currency_id
			# print 'cur====================', line.order_id.pricelist_id,cur
			res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
		# print 'res====================', res
		return res


	_columns = {
		'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
	}

	_defaults = {
        'product_qty': lambda *a: 0.0,
    }