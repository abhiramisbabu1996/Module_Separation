from openerp import models, fields, api, _


class ProductPriceData(models.Model):
	_name = 'product.price.data'

	product_id = fields.Many2one('product.product','Product')
	site_id = fields.Many2one('stock.location','Location')
	rate = fields.Float('Rate')
	qty = fields.Float('Quantity')
	date = fields.Datetime('Date')


	@api.multi
	def name_get(self):
		result = []
		for record in self:
			if record.product_id and record.site_id:
				result.append((record.id,u"%s (%s)" % (record.product_id.name, record.site_id.name)))
			
		return result