from openerp import models, fields, api


class PopupNotifications(models.Model):
	_name = 'popup.notifications'


	name = fields.Many2one('res.users','User')
	status = fields.Selection([('draft','Draft'),('shown','Shown')],default='draft')
	message = fields.Char('Message')
	message_bool = fields.Boolean(default=False)
	emi = fields.Boolean(default=False)
	pf_esi = fields.Boolean(default=False)
	veh_doc = fields.Boolean(default=False)
	emp_insu = fields.Boolean(default=False)

	# message_id = fields.Many2one('im_chat.message.req')
	# event_id = fields.Many2one('event.event')
	# event_bool = fields.Boolean(default=False)
	# site_id = fields.Many2one('task.entry')
	# site_bool = fields.Boolean(default=False)



	@api.multi
	def get_notifications(self):
		result = []
		for obj in self:
			result.append({
				'message': obj.message,
				'name':obj.name.name,
				'status': obj.status,
				'id': obj.id,
			})
		return result