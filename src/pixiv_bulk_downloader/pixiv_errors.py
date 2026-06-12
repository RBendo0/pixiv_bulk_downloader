

class PixivDownloaderError(Exception):
    """
    Classe base per tutte le eccezioni del downloader.
    """
    pass


class PixivApiError(PixivDownloaderError):
    """
    Errore durante comunicazione o elaborazione
    di una risposta proveniente dalle API Pixiv.
    """
    pass


class StorageError(PixivDownloaderError):
    """
    Errore durante accesso al filesystem,
    gestione checkpoint o serializzazione dati.
    """
    pass