# 500px.bundle
A channel plugin for [Plex Media Server](https://plex.tv/).

## Installation
Download and copy over to your plugins folder.

On Mac OS, it is:
````
~/Library/Application Support/Plex Media Server/Plug-ins/
````

On Windows 7, it is:
````
%LOCALAPPDATA%\Plex Media Server\Plug-ins\
````

## Implementation
The plugin is based on the [National Geographic plugin](https://github.com/plexinc-plugins/NationalGeographic.bundle).

Because 500px API requires OAuth, a workaround was implemented, which mimics what the browser does - it relies on the
cookies set by the server and extracts the CSRF token, which the API expects. This is undocumented usage of the API, which means
the plugin can break anytime in future.

## Known Issues / Limitations
* Only the first 100 photos are fetched (suggestions are accepted how to implement the paging in a plugin)
* No filtering based on categories can be done.
* Search is not supported.
* No access to the fresh, upcoming or editor's choice lists.
* Some photos are marked as Adult content. These require actual logged in access to view, which is not implemented yet.

## Thanks
[Plex Team](https://github.com/plexinc-plugins/NationalGeographic.bundle) - National Geographic plugin, which this plugin is based on.
