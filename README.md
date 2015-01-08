# 500px.bundle
A channel plugin for [Plex Media Server](https://plex.tv/).

## Installation
Follow the [Plex instructions for manually installing channels](https://support.plex.tv/hc/en-us/articles/201187656).

## Implementation
The plugin is based on the [National Geographic plugin](https://github.com/plexinc-plugins/NationalGeographic.bundle).

Because 500px API requires OAuth, a workaround was implemented, which mimics what the browser does - it relies on the cookies set by the server and extracts the CSRF token, which the API expects. This is undocumented usage of the API, which means the plugin can break anytime in future.

## Known Issues / Limitations
* Search is not supported.
* No access to the fresh, upcoming or editor's choice lists.
* Some photos are marked as Adult content. These require actual logged in access to view, which is not implemented yet.
* Thumbnails, which are marked as Adult content are not filtered.
* Thumbnails for categories, which have spaces in their names do not have thumbnails.

## Thanks
[Plex Team](https://github.com/plexinc-plugins/NationalGeographic.bundle) - National Geographic plugin, which this plugin is based on.