odoo.define("profiler.tour.profiler", function (require) {
    "use strict";

    var tour = require("web.Tour");

    tour.register({
        id: 'profile',
        name: "Profiler Tour",
        path: "/",
        mode: 'test',
        steps: [
            {
                title: "Start profiling",
                element: "#oe_systray li a.profiler_enable",
            },
            {
                title: "Stop profiling",
                element: "#oe_systray li a.profiler_disable",
            },
            {
                title: "Dump profiling",
                element: "#oe_systray li a.profiler_dump",
            },
            {
                title: "Clear profiling",
                element: "#oe_systray li a.profiler_clear",
            },
        ]
    });
});
