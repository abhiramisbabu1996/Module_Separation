from openerp import fields, models, api


class BudgetPlanningChartLine(models.Model):
    _name = 'budget.planning.chart.line'
    _rec_name = 'master_plan_line_id'

    project_id = fields.Many2one('project.project')
    mep = fields.Selection([('mechanical', 'Mechanical'), ('electricel', 'Electrical'), ('plumbing', 'Plumbing')])
    master_plan_id = fields.Many2one('master.plan')
    master_plan_line_id = fields.Many2one('master.plan.line', required=True)
    line_id = fields.Many2one('planning.chart')
    date = fields.Date('Date')
    work_id = fields.Char('Work Description')
    labour = fields.Float('No of Labours')
    # veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    qty = fields.Float('Qty')
    target_qty = fields.Float('Target Qty')
    material_qty = fields.Float('Material Qty')
    material = fields.Many2many('product.product', string='Materials')
    uom_id = fields.Many2one('product.uom', string="Units")
    working_hours = fields.Float('Working Hours')
    remarks = fields.Char('Remarks')
    sqft = fields.Float('Square Feet')
    estimated_cost = fields.Float()
    work_status = fields.Selection([('started', 'Started'),
                                    ('on_progressing', 'On Progressing'),
                                    ('partially_completed', 'Partially Completed'),
                                    ('completed', 'Completed')])
    plan_id = fields.Many2one('planning.chart.line')
    machinery_charge = fields.Float('Machinery Cost')
    total_charge = fields.Float('Total Cost')
    labour_charge = fields.Float('Labour Cost')

    @api.multi
    def open_view_wizard(self):
        for rec in self:
            res = {
                'name': 'Tasks',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'project.task',
                'target': 'new',
                'type': 'ir.actions.act_window',
                'context': {
                            'default_date_start':rec.date,
                            'default_date_end':rec.date,
                            # 'default_date_deadline':rec.date,
                            'default_project_id': rec.project_id.id,
                            'default_task_line_ids': [(0, 0, {'estimate_plan_line': rec.id,
                                                              'sqft': rec.sqft,
                                                              'no_labours': rec.labour,
                                                              'work_id': rec.master_plan_line_id.work_id.id,
                                                              'veh_categ_id': rec.veh_categ_id.ids,
                                                              'material': rec.material.ids,
                                                              'start_date': rec.date,
                                                              'finish_date': rec.date,
                                                              # 'subcontractor':rec.subcontractor,
                                                              'remarks_new': rec.remarks})]
                            }
            }

        return res
