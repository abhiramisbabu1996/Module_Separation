from openerp import fields, models, api

class ProjectProduct(models.Model):
    _name = 'project.product'


    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None: 
            context = {}
        line_num = 1    
    
        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context) 
            for line_rec in first_line_rec.project_id.project_product_ids: 
                line_rec.line_no = line_num 
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    name = fields.Many2one('product.product', 'Resource')
    quantity = fields.Float()
    unit_price = fields.Float()
    estimated_price = fields.Float()
    project_id = fields.Many2one('project.project')

    # @api.multi
    # @api.depends('project_id.task_ids.estimate_ids.qty')
    # def _compute_quantity(self):
    #     print "_compute_quantity ===================================================================",sadasd
    #     prod_dict = {}
    #     for task in self.project_id.task_ids:
    #         for estimate in task.estimate_ids:
    #             # qty = qty+estimate.product_qty
    #             # prod_dict.setdefault(estimate.pro_id, estimate.product_qty)
    #             if estimate.pro_id not in prod_dict:
    #                 prod_dict[estimate.pro_id] = estimate.qty
    #             else:
    #                 prod_dict[estimate.pro_id] = prod_dict[estimate.pro_id]+estimate.qty
    #             self.quantity = prod_dict[estimate.pro_id]

#     @api.multi
#     def project_estimation(self, project_id):
#         project = self.env['project.project'].browse(project_id)
# 
#         project_product_list = []
# 
#         for task in project.task_ids:
#             prod_dict = {}
#             for estimate in task.estimate_ids:
# 
#                 if estimate.pro_id not in prod_dict:
#                     prod_dict[estimate.pro_id] = estimate.qty
#                 else:
#                     prod_dict[estimate.pro_id] = prod_dict[estimate.pro_id]+estimate.qty
# 
#             for key, value in prod_dict.items():
#                 project_product_dict = {}
#                 project_product_dict['name'] = key.id
#                 project_product_dict['quantity'] = value
#                 project_product_dict['project_id'] = task.project_id.id
#                 project_product_list.append(project_product_dict)
# 
#         for rec in project_product_list:
#             # print 'rec', rec, sadasd
#             self.env['project.product'].create(rec)
