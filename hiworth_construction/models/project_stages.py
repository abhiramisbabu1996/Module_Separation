from openerp import models, fields, api

class ProjectStages(models.Model):
	_name = 'project.stage.prime'

	name = fields.Many2one('project.project','Project',required=True)
	contractor = fields.Many2one('res.partner',required=True)
	estimated_cost = fields.Float('Estimated Cost',required=True)
	stage_line = fields.One2many('stage.line.prime','stage_id',string="Stages")
	date = fields.Date('Date',default=fields.Date.today())
	location_id = fields.Many2one('stock.location','Location',related='name.location_id')
	manager_id = fields.Many2one('res.users','Manager',related="name.user_id")
	customer = fields.Many2one('res.partner','Manager',related="name.partner_id")
	date_start = fields.Date('Date Start',related="name.start_date")
	date_end = fields.Date('Date End',related="name.date_end")
	# building_no = fields.Char('Building Number',related="name.building_no")



class StageLine(models.Model):
	_name = 'stage.line.prime'

	stage_id = fields.Many2one('project.stage.prime')
	name = fields.Char('Stage',required=True)
	percent = fields.Float('Percentage',required=True)
	amount = fields.Float('Amount',compute="_compute_percent_amount")
	approximated_amnt = fields.Float('Approximated Amount',required=True)
	project = fields.Many2one('project.project',related='stage_id.name')
	amount_paid = fields.Float('Amount Paid')

	@api.multi
	def name_get(self):
		result = []
		for record in self:
			result.append((record.id,u"%s (%s)" % (record.stage_id.name.name, record.name)))
		return result

	@api.multi
	@api.depends('stage_id.estimated_cost','percent')
	def _compute_percent_amount(self):
		for record in self:
			print "self.stage_id.estimated_cost=============", record.stage_id.estimated_cost
			if record.stage_id.estimated_cost != 0:
				record.amount = (record.percent/100)*record.stage_id.estimated_cost
				print "self.amount============", record.amount
