from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime



class TaskReportWizard(models.TransientModel):
    _name = 'task.report.wizard'

    company_id = fields.Many2one('res.company', 'Company')
    categ_id = fields.Many2one('task.category', 'Category')
    project_id = fields.Many2one('project.project', 'Project')
    subcategory_wise = fields.Boolean('Sub category wise')

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        }


    @api.multi
    def print_task_estimation(self):
        self.ensure_one()

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.task_estimation_report_template',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
        }

    @api.multi
    def view_task_estimation(self):
        self.ensure_one()
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.task_estimation_report_template',
            'datas': datas,
            'report_type': 'qweb-html',
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
        }


    @api.multi
    def get_tasks(self):
        self.ensure_one()
        # main_list = []
        # sub_list = []
        task_obj = self.env['project.task']
        if self.subcategory_wise == False:
            tasks = task_obj.search([('project_id','=',self.project_id.id),('categ_id','=',self.categ_id.id)])
        if self.subcategory_wise == True:
            tasks = task_obj.search([('project_id','=',self.project_id.id),('sub_categ_id','=',self.categ_id.id)])
        # main_dict = {}
        # for task in tasks:
        #     list = filter(lambda dict: dict['main_categ'] == task.categ_id.name, main_list)
        #     if len(list) == 0:
        #         main_list.append({'main_categ':task.categ_id.name})
        #     print 'list===============', list, asdasd
            # if task.categ_id.id not in main_list:
            #     main_list.append({'main_categ':task.categ_id.name, 'sub_list':})
        return tasks
