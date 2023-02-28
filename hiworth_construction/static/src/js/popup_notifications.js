openerp.hiworth_construction = function(instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

instance.web.WebClient = instance.web.WebClient.extend({
    get_notif_box: function(me) {
            return $(me).closest(".ui-notify-message-style");
        },

    check_hiworth_construction: function () {
        var self = this;

        
        this.rpc('/hiworth_construction/notify_msg')
        .done(
            function (notify_msg) {
                _.each(notify_msg,  function(notif) {
                    setTimeout(function() {
                        //desktop notification declaration{
                        var notification = new Notification(notif.name, {
                          icon: '/hiworth_construction/static/src/img/envelope.png',
                          body: notif.message,
                        });
                        //}
                        if ($('.ui-notify-message p#p_id').filter(function () {
                            return $(this).html() == notif.id;
                        }).length) {
                            return;
                        } 
                        notif.title = QWeb.render('popup_title', {'name':notif.name,'message': notif.message, 'id': notif.id});
                        notif.message = QWeb.render('popup_footer_msg');
                        notif_elem = self.do_notify(notif.title, notif.message, true);
                        notif_elem.element.find(".link2showed").on('click',function() {
                        self.get_notif_box(this).find('.ui-notify-close').trigger("click");
                        self.rpc("/hiworth_construction/notify_msg_ack", {'notif_id': notif.id});
                        });
                    }); 
                });
            }
        )
       

        .fail(function (err, ev) {
            if (err.code === -32098) {
                ev.preventDefault();
            }
        });
    },

    start: function (parent) {
        var self = this;
        self._super(parent);
        $(document).ready(function () {
            self.check_hiworth_construction();
            setInterval( function() {
                self.check_hiworth_construction();
            }, 3 * 1000);
        });
    },

})};


