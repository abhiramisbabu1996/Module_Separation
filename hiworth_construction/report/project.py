from openerp import fields, models, api

class ProjectProject(models.Model):
    _inherit='project.project'

    # @api.model
    # def get_project_tasks(self, project_id):
    #     return self.env['project.task'].search([('project_id','=',project_id)])
    #
    # @api.model
    # def get_project_status(self, project_id):
    #     return self.env['project.project'].browse(project_id).stage_id
    #
    # @api.model
    # def get_project_account_statement(self, project_id):
    #     return self.env['project.project'].browse(project_id).acc_statement
    #
    # @api.model
    # def get_project_schedule(self, project_id):
    #     return self.env['project.project'].browse(project_id).schedule_id
    @api.model
    def get_project_categories(self, project_id):
        project = self.env['project.project'].browse(project_id)
        return list({task.categ_id for task in project.task_ids})
        # print self.env['task.category'].search([('categ_id','in',project.task_ids._ids)]),'asdas',asad
        # return self.env['project.task'].search([('categ_id','in',project.task_ids._ids)])

    @api.model
    def get_category_estimation(self, category):
        # [{'name':name, 'quantity':quantity} for ]
        # for task in category.task_ids:
        #     for estimate in task.estimate_ids
        #
        prod_dict = {}

        for task in category.task_ids:
            for estimate in task.estimate_ids:
                if estimate.pro_id not in prod_dict:
                    prod_dict[estimate.pro_id] = estimate.qty
                else:
                    prod_dict[estimate.pro_id] = prod_dict[estimate.pro_id]+estimate.qty
        return prod_dict
        # print self.env['task.category'].search([('categ_id','in',project.task_ids._ids)]),'asdas',asad
        # return self.env['project.task'].search([('categ_id','in',project.task_ids._ids)])
