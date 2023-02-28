from openerp import fields, models, api

class ProductCategoryList(models.Model):
    _name = 'product.category.list'

    @api.onchange('name')
    def onchange_category_list(self):
        for rec in self:
            if rec.name:
                product_list = self.env['product.product'].search([('categ_id','=',rec.name.id)])
                value_list = []
                values ={}
                for prod in product_list:
                    values.update({'product_id':prod.id,})
                    value_list.append((0,0,values))
                rec.product_category_list_line_ids = value_list

    name=fields.Many2one('product.category')
    product_category_list_line_ids = fields.One2many('product.category.list.line','product_category_id',"Category Lines")

class ProductCategoryListLine(models.Model):
    _name = 'product.category.list.line'

    product_category_id = fields.Many2one('product.category.list',"Product Category")
    product_id = fields.Many2one('product.product',"Products")