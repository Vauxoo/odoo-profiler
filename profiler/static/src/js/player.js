odoo.define('profiler', function(require) {
    "use strict";
    var webclient = require('web.web_client');
    var UserMenu = require('web.UserMenu');
    var profiler = require('profiler.player');

    UserMenu.include({
        do_update: function () {
            var self = this;
            self.rpc('/web/profiler/initial_state', {}).done(function(state) {
                if (state.has_player_group) {
                    this.profiler_player = new profiler.ProfilerPlayer(this);
                    // Enterprise path
                    this.profiler_player.prependTo(webclient.$('.o_menu_systray'));
                    // Community path
                    this.profiler_player.prependTo(webclient.$('.oe_systray'));
                    this.profiler_player.apply_class(state.player_state);
                }
            });
            return this._super();
        },
    });
});
