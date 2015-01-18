from urllib import quote

# Plex Media Server shared code import
api = SharedCodeService.px500api
parse = SharedCodeService.px500parse

PHOTOS_PER_PAGE = 100

ICON = '500px_logo.png'
NEXT_ICON = 'next_icon_bl.png'

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
	HTTP.CacheTime = CACHE_1HOUR

def get_csrf_token():
	token = Dict['csrf_token']
	token = api.get_csrf_token(token)
	Dict['csrf_token'] = token
	return token 

def get_category_param(category):
	return '' if api.CATEGORIES[0] == category else category

def get_category_thumb(category):
	try:
		thumb_key = 'thumb_' + category
		thumb_url = Dict[thumb_key]
		if thumb_url:
			return thumb_url
		csrf_token = get_csrf_token()
		category_param = quote(get_category_param(category))
		response = JSON.ObjectFromURL(api.PHOTOS_URL.format(
			page = 1,
			feature = api.PHOTOS_FEATURE,
			token = csrf_token,
			results_per_page = 1,
			category = category_param))
		if len(response['photos']) < 1:
			return None
		thumb_url = response['photos'][0]['image_url'][0]
		Dict[thumb_key] = thumb_url
		return thumb_url
	except Exception as e:
		Log.Warn("Failed to fetch thumbnail for %s category: %s", category, e)
		return None

####################################################################################################
@handler('/photos/500px', L('ChannelName'), thumb = ICON)
def PhotosMainMenu():
	oc = ObjectContainer(view_group='Pictures', title2=L("PopularPhotosName"))
	oc.add(SearchDirectoryObject(identifier="com.github.dnachev.plex.plugins.500px", title=L("SearchTitle"), prompt=L("SearchPrompt")))

	for category in api.CATEGORIES:
		if api.CATEGORIES[0] == category:
			thumb_url = R(ICON)
		else:
			thumb_url = get_category_thumb(category)
		Log.Debug('Category %s thumbnail: %s', category, thumb_url)
		oc.add(DirectoryObject(key = Callback(CategorizedPhotos, category = category), title = category, thumb = thumb_url))

	return oc

####################################################################################################
@route('/photos/500px/{category}', page = int, allow_sync = False)
def CategorizedPhotos(category = api.CATEGORIES[0], page = 1):

	Log.Debug('Request category: %s, page: %d', category, page)

	# 500px API requires authenticity_token parameter attached to all requests, which are made to the API.
	# This authenticity_token is actually available in every page, which https://500px.com returns and it is
	# used as standard defence against CSRF requests. The plugin simply fetches a page and extract the token
	# and then attaches to the normal 500px API request.

	csrf_token = get_csrf_token()
	category_param = quote(get_category_param(category)) # The category is not urlencoded by the HTTP library
	response = JSON.ObjectFromURL(api.PHOTOS_URL.format(
			page = page,
			feature = api.PHOTOS_FEATURE,
			results_per_page = PHOTOS_PER_PAGE,
			token = csrf_token,
			category = category_param
		), cacheTime = 0)
	Log("Fetched %d photos out of %d spread over %d pages.", len(response["photos"]), response["total_items"], response["total_pages"])
	photos = parse.parse_photos(response['photos'])
	oc = ObjectContainer(view_group='List', title2=category, objects=photos)
	total_pages = response["total_pages"]
	if page + 1 < total_pages:
		page = page + 1
		oc.add(NextPageObject(key = Callback(CategorizedPhotos, category = category, page = page), title = L("NextPage"), thumb = R(NEXT_ICON)))
			
	return oc
