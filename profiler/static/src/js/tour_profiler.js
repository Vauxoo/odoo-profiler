odoo.define("profiler.tour.profiler", function (require) {
    "use strict";

    var core = require("web.core");
    var tour = require("web_tour.tour");
    var base = require("web_editor.base");
    var _t = core._t;

    tour.register("profile", {
        test: true,
        url: "/",
        wait_for: base.ready(),
    },
        [
            {
                content: "Start profiling",
                trigger: ".o_menu_systray li a.profiler_enable",
            },
            {
                content: "Stop profiling",
                trigger: ".o_menu_systray li a.profiler_disable",
            },
            {
                content: "Dump profiling",
                trigger: ".o_menu_systray li a.profiler_dump",
            },
            {
                content: "Clear profiling",
                trigger: ".o_menu_systray li a.profiler_clear",
            },
        ]
    );
});
