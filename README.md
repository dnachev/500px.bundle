# 500px.bundle
A channel plugin for [Plex Media Server](https://plex.tv/).

## Features
* Listing all popular photos
* List popular photos per category
* Search photos

## Installation
Follow the [Plex instructions for manually installing channels](https://support.plex.tv/hc/en-us/articles/201187656).

## Implementation
The plugin is based on the [National Geographic plugin](https://github.com/plexinc-plugins/NationalGeographic.bundle).

Because 500px API requires OAuth, a workaround was implemented, which mimics what the browser does - it relies on the cookies set by the server and extracts the CSRF token, which the API expects. This is undocumented usage of the API, which means the plugin can break anytime in future.

## Known Issues / Limitations
* No access to the fresh, upcoming or editor's choice lists.
* Some photos are marked as Adult content. These require actual logged in access to view, which is not implemented yet.

## Thanks
[Plex Team](https://github.com/plexinc-plugins/NationalGeographic.bundle) - National Geographic plugin, which this plugin is based on.