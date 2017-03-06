odoo.define('odoo-profiler', function(require) {
    "use strict";

    var Widget = require('web.Widget');
    var UserMenu = require('web.UserMenu');
    var webclient = require('web.web_client');

    var ProfilerPlayer = Widget.extend({
        template: 'profiler.player',
        events: {
            "click .profiler_enable": "enable",
            "click .profiler_disable": "disable",
            "click .profiler_clear": "clear",
            "click .profiler_dump": "dump",
        },
        apply_class: function(css_class) {
            this.$el.removeClass('profiler_player_enabled');
            this.$el.removeClass('profiler_player_disabled');
            this.$el.removeClass('profiler_player_clear');
            this.$el.addClass(css_class);
        },
        enable: function() {
            this.rpc('/web/profiler/enable', {});
            this.apply_class('profiler_player_enabled');
        },
        disable: function() {
            this.rpc('/web/profiler/disable', {});
            this.apply_class('profiler_player_disabled');
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

    UserMenu.include({
        do_update: function () {
            var self = this;
            this.update_promise.done(function () {
                self.rpc('/web/profiler/initial_state', {}).done(function(state) {
                    if (state.has_player_group) {
                        this.profiler_player = new ProfilerPlayer(this);
                        this.profiler_player.prependTo(webclient.$('.oe_systray'));
                        this.profiler_player.apply_class(state.player_state);
                    }
                });
            });
            return this._super();
        },
    });
});
