import openerp
import openerp.http as http
from openerp.http import request


class PopupController(openerp.http.Controller):

    @http.route('/hiworth_construction/notify_msg', type='json', auth="none")
    def notify_msg(self):
        # print 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        user_id = request.session.get('uid')
        return request.env['popup.notifications'].sudo().search(
            [('status', '!=', 'shown'),('name','=',user_id)]
        ).get_notifications()

    @http.route('/hiworth_construction/notify_msg_ack', type='json', auth="none")
    def notify_msg_ack(self, notif_id, type='json'):
        notif_obj = request.env['popup.notifications'].sudo().browse([notif_id])
        if notif_obj:
            notif_obj.status = 'shown'
            if notif_obj.message_bool == True:
               notif_obj.message_id.status = 'shown'
           
            notif_obj.unlink()