odoo.define('profiler.website', function (require) {
    'use strict';

    var profiler = require('profiler.player');
    var ajax = require('web.ajax');
    var core = require('web.core');
    // wait for implicit dependencies to load
    require('web_editor.base');
    var qweb = core.qweb;

    if(!$('#oe_main_menu_navbar').length) {
        return false;
    }

    return ajax.loadXML('/profiler/static/src/xml/player.xml', qweb).then(function() {
        var profilerPlayer = new profiler.ProfilerPlayer();
        profilerPlayer.rpc('/web/profiler/initial_state', {}).done(function(state) {
            if (state.has_player_group) {
                profilerPlayer.prependTo($('#oe_systray'));
                profilerPlayer.apply_class(state.player_state);
            }
        });
    });

});
