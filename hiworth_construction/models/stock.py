from openerp import fields, models, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    project_id = fields.Many2one('project.project')
    project_site_store_id = fields.Many2one('stock.location')