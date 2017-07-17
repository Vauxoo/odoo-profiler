(function() {
    'use strict';
    function apply_class(css_class, el) {
        var self = el;
        self.removeClass('profiler_player_enabled');
        self.removeClass('profiler_player_disabled');
        self.removeClass('profiler_player_clear');
        self.removeClass('hide');
        self.addClass(css_class);
    }
    openerp.website.if_dom_contains('.oe_topbar_item', function(){

        var set_buttons = $('.oe_topbar_item.profiler_player');
         openerp.jsonRpc('/web/profiler/initial_state', {}).done(function(state) {
            if (state.has_player_group) {
                apply_class(state.player_state, set_buttons);
            }
        });
        set_buttons.on('click', '.profiler_enable', function (obj){
            openerp.jsonRpc('/web/profiler/enable', {});
            apply_class('profiler_player_enabled', set_buttons);
        });
        set_buttons.on('click', '.profiler_disable', function (obj){
            var self = $(obj.target);
            openerp.jsonRpc('/web/profiler/disable', {});
            apply_class('profiler_player_disabled', set_buttons);
        });
        set_buttons.on('click', '.profiler_clear', function (obj){
            var self = $(obj.target);
            openerp.jsonRpc('/web/profiler/clear', {});
            apply_class('profiler_player_clear', set_buttons);
        });
        set_buttons.on('click', '.profiler_dump', function (){
            var id = _.uniqueId('get_file_frame'),
                token = new Date().getTime(),
                form = $('<form>', {
                    action:'/web/profiler/dump',
                    method: "POST",
                }).appendTo(document.body),
                input = $('<input type="hidden" name="token">');
            input.val(token).appendTo(form);
            form.attr('target', id).get(0).submit();
        });

    });
}());
