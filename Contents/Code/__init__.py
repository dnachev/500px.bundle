from urllib import quote
import time

# Plex Media Server shared code import
api = SharedCodeService.px500api
parse = SharedCodeService.px500parse

PHOTOS_PER_PAGE = 100

ICON = '500px_logo.png'
NEXT_ICON = 'next_icon_bl.png'

THUMBNAIL_CACHE_TIME = CACHE_1HOUR # seconds
THUMBNAIL_TIMEOUT = 10 # seconds

NAME = L("Title")

class Future:
	"""
	Simple class to encapsulate the communication between two threads (producer, consumer)

	The class has two main methods: get() and set(). get() will block the calling thread until set is called or
	specified timeout has expired. If set() has been called before get(), then the method will return
	the value immediatelly.

	The return value of get() is either the value set using set() or None.

	The users of this class must ensure that get() and set() are to be called in separate threads or set() is
	called before get(). Failing to satisfy this requirement, deadlock will occur.
	"""
	def __init__(self):
		self.value = None
		self.event = Thread.Event()

	def get(self, timeout = None):
		self.wait(timeout)
		return self.value

	def set(self, value):
		self.value = value
		self.event.set()

	def wait(self, timeout = None):
		self.event.wait(timeout)


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

def get_csrf_token(validate = True):
	token = Dict['csrf_token']
	if not validate and token:
		# If we have a token and we don't need to be validated, return immediatelly
		return token
	token = api.get_csrf_token(token)
	Dict['csrf_token'] = token
	return token

def get_category_param(category):
	return '' if api.CATEGORIES[0] == category else category

def get_thumbnail_url_from_cache(category):
	# The thumbnails URL are cached using tuples, together with the
	# timestamp when they were retrieved. The tuple look like:
	#  (url, timestamp)
	# TODO Ensure thread-safety when accessing Dict service
	cache = Dict['thumbnail_cache']
	if not cache:
		Dict['thumbnail_cache'] = cache = {}
	if category in cache:
		cache_entry = cache[category]
		if cache_entry[1] + THUMBNAIL_CACHE_TIME >= time.time():
			return cache_entry[0]
		Log.Debug("Thumbnail for %s found, but it was expired. Reloading...", category)
	return None

def set_thumbnail_url_in_cache(category, url):
	# TODO Ensure thread-safety when accessing Dict service
	cache = Dict['thumbnail_cache']
	if not cache:
		Dict['thumbnail_cache'] = cache = {}
	cache[category] = (url, time.time())

def get_thumbnail_url(category):
	try:
		# CSRF token is not validated, it's expected it is fresh before
		# calling this method
		csrf_token = get_csrf_token(False)
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
		set_thumbnail_url_in_cache(category, thumb_url)
		return thumb_url
	except Exception as e:
		Log.Warn("Failed to fetch thumbnail for %s category: %s", category, e)
		return None

def schedule_thumbnail_url_retrieval(category, future):
	url = get_thumbnail_url(category)
	future.set(url)

def get_category_thumbnail(category):
	"""
	Returns Future resolved with the thumbnail URL if any.
	"""
	result = Future()
	cached_url = get_thumbnail_url_from_cache(category)
	if cached_url:
		result.set(cached_url)
		return result
	Thread.Create(schedule_thumbnail_url_retrieval, globalize=False, category = category, future = result)
	return result
		

####################################################################################################
@handler('/photos/500px', L('ChannelName'), thumb = ICON)
def PhotosMainMenu():
	oc = ObjectContainer(view_group='Pictures', title2=L("PopularPhotosName"))
	oc.add(SearchDirectoryObject(identifier="com.github.dnachev.plex.plugins.500px", title=L("SearchTitle"), prompt=L("SearchPrompt")))
	all_category = api.CATEGORIES[0]
	oc.add(DirectoryObject(key = Callback(CategorizedPhotos, category = all_category), title = all_category, thumb = R(ICON)))
	thumbnails = {}
	# Ensure there is a fresh token in the cache before fetching the thumbnails
	get_csrf_token()
	for category in api.CATEGORIES:
		if all_category == category:
		 	continue;
		thumbnails[category] = get_category_thumbnail(category)

	for category in thumbnails:
		start = time.time()
		thumb_url = thumbnails[category].get(THUMBNAIL_TIMEOUT)
		Log.Debug('Fetched %s thumbnail %s for %d sec.', category, thumb_url, time.time() - start)
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
