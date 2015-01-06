from urllib import quote

API_URL = "https://api.500px.com/v1"
PHOTOS_URL = API_URL + "/photos?page={page}&feature={feature}&rpp={results_per_page}&authenticity_token={token}&image_size[]=3"
PHOTO_URL = "https://500px.com/photo/{id}"
LOGIN_URL = API_URL + "/session"

CSRF_TOKEN_URL = "https://500px.com/popular"
PHOTOS_PER_PAGE = 100

ICON = '500px_logo.png'

NAME = L("Title")
####################################################################################################
def Start():

	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	Plugin.AddViewGroup("Pictures", viewMode="Pictures", mediaType="photos")

	# Set the default ObjectContainer attributes
	ObjectContainer.title1 = NAME
	ObjectContainer.view_group = "List"

	# Set the default cache time
	HTTP.CacheTime = 1

####################################################################################################
'''
Validates the CSRF token we have stored by making a small request to the 500px API.

Returns True if the token can be used for API requests, False otherwise.
'''
def validate_csrf_token(token):
	if not token:
		return False
	try:
		Log.Debug("Validating token %s...", token)
		response = HTTP.Request(PHOTOS_URL.format(
			token = token,
			feature = 'popular',
			page = 1,
			results_per_page = 1,
		), cacheTime=1, immediate=True)
		Log.Debug("Validation is successful.")
		return True
	except Exception as e:
		Log.Info("Validation of %s failed: %s", token, e)
		return False

'''
Returns CSRF token, which 500px API requires for making requests.

The token is cached in Plex Dict object and will be reused if possible.

This function should be called once for a single Plex request.
'''
def get_csrf_token():
	csrf_token = Dict['csrf_token']
	if validate_csrf_token(csrf_token):
		return csrf_token
	Log.Info("Token expired. Retrieving CSRF token from one 500px page...");
	# TODO Validate existing CSRF token before returning using ping
	csrf_request = HTTP.Request(CSRF_TOKEN_URL, headers = { 'Accept': "text/html" }, cacheTime = 1, immediate = True)
	csrf_page_content = csrf_request.content;
	csrf_page = HTML.ElementFromString(csrf_page_content)
	csrf_token_element = csrf_page.xpath("//meta[@name='csrf-token']")[0]
	csrf_token = csrf_token_element.get("content")
	Log.Info("Token found: %s", str(csrf_token))
	Log.Debug("Available cookies: %s", str(HTTP.CookiesForURL("https://500px.com/popular")))
	Dict['csrf_token'] = csrf_token
	return csrf_token

####################################################################################################
@handler('/photos/500px', L('ChannelName'), thumb = ICON)
def PhotosMainMenu():
	oc = ObjectContainer(view_group='Pictures', no_cache=True, title2=L("PopularPhotosName"))

	# 500px API requires authenticity_token parameter attached to all requests, which are made to the API.
	# This authenticity_token is actually available in every page, which https://500px.com returns and it is
	# used as standard defence against CSRF requests. The plugin simply fetches a page and extract the token
	# and then attaches to the normal 500px API request.

	csrf_token = get_csrf_token()
	# The token needs to be urlencoded as the HTTP library won't do it
	csrf_token = quote(str(csrf_token))
	Log.Debug("Encoded token: %s", csrf_token)
	response = JSON.ObjectFromURL(PHOTOS_URL.format(
			page = 1,
			feature = "popular",
			results_per_page = PHOTOS_PER_PAGE,
			token = csrf_token
		), cacheTime = 0)
	Log("Fetched %d photos out of %d spread over %d pages.", len(response["photos"]), response["total_items"], response["total_pages"])
	for photo in response["photos"]:
		Log.Debug("Parsing photo JSON object: %s", JSON.StringFromObject(photo))
		title = photo["name"]
		url = PHOTO_URL.format(id = photo["id"])
		thumb = photo["image_url"][0]
		description = photo["description"]
	
		date = None
		try:
			date = Datetime.ParseDate(photo["created_at"])
		except:
			Log.Debug('Cannot parse date %s', photo["created_at"])

		oc.add(PhotoObject(
			url = url,
			title = title,
			summary = description,
			thumb = thumb,
			originally_available_at = date))
			
	return oc
