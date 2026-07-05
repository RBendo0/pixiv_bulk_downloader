from __future__ import annotations

from pixiv_bulk_downloader.my_gppt import PixivAuth


ILLUST_ID = 139517159


def main() -> None:
    aapi, login_info = PixivAuth().auth()

    print("AUTH OK")
    print("USER:", login_info["response"]["user"]["id"])

    result = aapi.illust_bookmark_add(
        ILLUST_ID,
        restrict="private",
    )

    print("RESULT TYPE:", type(result).__name__)
    print(result)

    if isinstance(result, dict) and "error" in result:
        print("ERROR PAYLOAD:")
        print(result["error"])


if __name__ == "__main__":
    main()