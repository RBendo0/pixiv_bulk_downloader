Sì. Nei moduli caricati risultano queste chiamate API Pixiv:

Login

PixivAuth().auth() in main.py
Nota: il modulo my_gppt.py non è tra quelli caricati, quindi per ora vedo solo il punto di ingresso del login.

Bookmarks / fetch

self.aapi.user_detail(self.aapi.user_id)
self.aapi.user_bookmarks_illust(target_id, restrict=restrict)
self.aapi.parse_qs(next_json.get("next_url"))
self.aapi.user_bookmarks_illust(**next_qs)

Ugoira / download

self.aapi.ugoira_metadata(_id_)
self.aapi.download(...), già tramite call_download_api(...)

Modifica account

self.aapi.illust_bookmark_add(...)

Quindi il futuro pixiv_call_api.py deve coprire almeno questi casi.