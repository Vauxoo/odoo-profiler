openerp.profiler.player = function(instance) {
    instance.profiler.Player = instance.web.Widget.extend({
        template: 'profiler.player',
        events: {
            "click .profile_enable": "enable",
            "click .profile_disable": "disable",
            "click .profile_clear": "clear",
            "click .profile_dump": "dump",
        },
        enable: function() {
            console.log('enable')
            this.rpc('/web/profiler/enable', {});
        },
        disable: function() {
            console.log('disable')
            this.rpc('/web/profiler/disable', {});
        },
        clear: function() {
            console.log('clear')
            this.rpc('/web/profiler/clear', {});
        },
        dump: function() {
            console.log('dump')
            $.blockUI();
            this.session.get_file({
                url: '/web/profiler/dump',
                complete: $.unblockUI
            });
        },
    });

    instance.web.UserMenu.include({
        do_update: function () {
            this.update_promise.done(function () {
                this.profiler_player = new instance.profiler.Player(this);
                this.profiler_player.prependTo(instance.webclient.$('.oe_systray'));
            });
            return this._super();
        },
    });
};
