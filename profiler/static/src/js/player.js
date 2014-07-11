openerp.profiler.player = function(instance) {
    instance.profiler.Player = instance.web.Widget.extend({
        template: 'profiler.player',
        events: {
            "click .profiler_enable": "enable",
            "click .profiler_disable": "disable",
            "click .profiler_clear": "clear",
            "click .profiler_dump": "dump",
        },
        apply_class: function(css_class) {
            this.$el.removeClass('profiler_player_enable');
            this.$el.removeClass('profiler_player_disable');
            this.$el.removeClass('profiler_player_clear');
            this.$el.addClass(css_class);
        },
        enable: function() {
            this.rpc('/web/profiler/enable', {});
            this.apply_class('profiler_player_enable');
        },
        disable: function() {
            this.rpc('/web/profiler/disable', {});
            this.apply_class('profiler_player_disable');
        },
        clear: function() {
            this.rpc('/web/profiler/clear', {});
            this.apply_class('profiler_player_clear');
        },
        dump: function() {
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
