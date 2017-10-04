odoo.define('profiler', function(require) {
    "use strict";
    var profiler = require('profiler.player');
    var SystrayMenu = require('web.SystrayMenu');

    SystrayMenu.Items.push(profiler.ProfilerPlayer);
});
