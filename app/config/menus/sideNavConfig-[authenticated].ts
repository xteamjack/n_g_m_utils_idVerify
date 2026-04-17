export const sideNavConfig = {
    inheritance: 'merge',
    type: 'simple',
    orientation: 'vertical',
    behaviors: ['expandCollapse', 'sections'],
    middle: {
        generic: [],
        modules: {
            'Control Center': {
                title: "Control Center",
                icon: "i-sans-settings",
                appKey: "config",
                group: true,
                children: [
                    { title: "Apps", url: "/config/apps", icon: "i-sans-app" },
                    { title: "Storage", url: "/config/storage", icon: "i-sans-storage" }
                ]
            },
            'Notifications': {
                title: "Notifications",
                icon: "i-sans-notification",
                appKey: "notify",
                group: true,
                children: [
                    { title: "Logs", url: "/notify/logs", icon: "i-sans-list" },
                    { title: "Whatsapp Chat", url: "/notify/whatsappChat", icon: "i-sans-whatsapp" }
                ]
            },
            'Entity Explorer': {
                title: "Entity Explorer",
                icon: "i-sans-search",
                appKey: "entityExplorer",
                group: true,
                children: [
                    { title: "Dashboard", url: "/entityExplorer/dashboard", icon: "i-sans-dashboard" },
                    { title: "Objects", url: "/entityExplorer/objects", icon: "i-sans-collection" }
                ]
            }
        }
    }
};
