odoo.define('profiler.player', function (require) {
    'use strict';

    var Widget = require('web.Widget');
    var ajax = require('web.ajax');

    var ProfilerPlayer = Widget.extend({
        template: 'profiler.player',
        events: {
            "click .profiler_enable": "enable",
            "click .profiler_disable": "disable",
            "click .profiler_clear": "clear",
            "click .profiler_dump": "dump",
        },
        start: function(){
            var self = this;
            self._rpc({route: '/web/profiler/initial_state'}).then(function(state) {
                if (state.has_player_group) {
                    self.apply_class(state.player_state);
                }
            });
            return this._super.apply(this, arguments);

        },
        apply_class: function(css_class) {
            this.$el.removeClass('profiler_player_enabled');
            this.$el.removeClass('profiler_player_disabled');
            this.$el.removeClass('profiler_player_clear');
            this.$el.addClass(css_class);
        },
        enable: function() {
            this._rpc({route: '/web/profiler/enable'});
            this.apply_class('profiler_player_enabled');
        },
        disable: function() {
            this._rpc({route: '/web/profiler/disable'});
            this.apply_class('profiler_player_disabled');
        },
        clear: function() {
            this._rpc({route: '/web/profiler/clear'});
            this.apply_class('profiler_player_clear');
        },
        dump: function() {
            $.blockUI();
            if (typeof this.session === "undefined"){
                ajax.get_file({
                    url: '/web/profiler/dump',
                    complete: $.unblockUI
                });
            }else {
                this.session.get_file({
                    url: '/web/profiler/dump',
                    complete: $.unblockUI
                });
            }
        },
    });

    return {
        ProfilerPlayer: ProfilerPlayer,
    };
});

