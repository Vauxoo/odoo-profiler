odoo.define('profiler.website', function (require) {
    'use strict';

    var profiler = require('profiler.player');
    var Widget = require('web.Widget');
    var session = require('web.session');
    var websiteNavbarData = require('website.navbar');

    if (!session.is_system) {
        return;
    }

    var ProfilerMenu = Widget.extend({
        xmlDependencies: ['/profiler/static/src/xml/player.xml'],
        start: function () {
            var profilerPlayer = new profiler.ProfilerPlayer(this);
            return $.when(
                this._super.apply(this, arguments),
                    profilerPlayer.prependTo(this.$el)
            );
        },
    });

    websiteNavbarData.websiteNavbarRegistry.add(ProfilerMenu, '.o_menu_systray');

    return {
        ProfilerMenu: ProfilerMenu
    };

});
