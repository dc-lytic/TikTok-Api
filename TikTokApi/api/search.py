from __future__ import annotations
from urllib.parse import urlencode
from typing import TYPE_CHECKING, Iterator
from .user import User
from .video import Video
from .keywordsuggestion import KeywordSuggestion
from ..exceptions import InvalidResponseException

if TYPE_CHECKING:
    from ..tiktok import TikTokApi


class Search:
    """Contains static methods about searching TikTok for a phrase."""

    parent: TikTokApi

    @staticmethod
    async def users(search_term, count=10, cursor=0, **kwargs) -> Iterator[User]:
        """
        Searches for users.

        Note: Your ms_token needs to have done a search before for this to work.

        Args:
            search_term (str): The phrase you want to search for.
            count (int): The amount of users you want returned.

        Returns:
            async iterator/generator: Yields TikTokApi.user objects.

        Raises:
            InvalidResponseException: If TikTok returns an invalid response, or one we don't understand.

        Example Usage:
            .. code-block:: python

                async for user in api.search.users('david teather'):
                    # do something
        """
        async for user in Search.search_type(
            search_term, "user/full", count=count, cursor=cursor, **kwargs
        ):
            yield user

    @staticmethod
    async def general(search_term, count=9, cursor=0, **kwargs) -> Iterator[Video]:
        """
        Searches for videos on home page.

        Note: Your ms_token needs to have done a search before for this to work.

        Args:
            search_term (str): The phrase you want to search for.
            count (int): The amount of vidoes you want returned.

        Returns:
            async iterator/generator: Yields TikTokApi.video objects.

        Raises:
            InvalidResponseException: If TikTok returns an invalid response, or one we don't understand.

        Example Usage:
            .. code-block:: python

                async for user in api.search.users('david teather'):
                    # do something
        """
        if count > 9:
            Search.parent.logger.warning(
                "TikTok only allows a maximum of 9 videos to be returned per search without login."
            )
        async for video in Search.search_type(
                search_term, "general/full", count=count, cursor=cursor, **kwargs
        ):
            yield video

    @staticmethod
    async def keyword_suggestion(search_term, count=8, cursor=0, **kwargs) -> Iterator[KeywordSuggestion]:
        """
        Searches for keyword suggestions on home page.

        Note: Your ms_token needs to have done a search before for this to work.

        Args:
            search_term (str): The phrase you want to search for.
            count (int): The amount of keywords you want returned.

        Returns:
            async iterator/generator: Yields TikTokApi.KeywordSuggestion objects.

        Raises:
            InvalidResponseException: If TikTok returns an invalid response, or one we don't understand.

        Example Usage:
            .. code-block:: python

                async for user in api.search.users('david teather'):
                    # do something
        """
        async for video in Search.search_type(
                search_term, "general/preview", count=count, cursor=cursor, **kwargs
        ):
            yield video

    @staticmethod
    async def search_type(
        search_term, obj_type, count=10, cursor=0, **kwargs
    ) -> Iterator:
        """
        Searches for a specific type of object. But you shouldn't use this directly, use the other methods.

        Note: Your ms_token needs to have done a search before for this to work.
        Note: Currently only supports searching for users, other endpoints require auth.

        Args:
            search_term (str): The phrase you want to search for.
            obj_type (str): The type of object you want to search for (user)
            count (int): The amount of users you want returned.
            cursor (int): The the offset of users from 0 you want to get.

        Returns:
            async iterator/generator: Yields TikTokApi.video objects.

        Raises:
            InvalidResponseException: If TikTok returns an invalid response, or one we don't understand.

        Example Usage:
            .. code-block:: python

                async for user in api.search.search_type('david teather', 'user'):
                    # do something
        """
        found = 0
        while found < count:
            params = {
                "keyword": search_term,
                "cursor": cursor,
                "from_page": "search",
                "web_search_code": """{"tiktok":{"client_params_x":{"search_engine":{"ies_mt_user_live_video_card_use_libra":1,"mt_search_general_user_live_card":1}},"search_server":{}}}""",
            }

            resp = await Search.parent.make_request(
                url=f"https://www.tiktok.com/api/search/{obj_type}/",
                params=params,
                headers=kwargs.get("headers"),
                session_index=kwargs.get("session_index"),
            )
            print("RESPONSE: ", resp)

            if resp is None:
                raise InvalidResponseException(
                    resp, "TikTok returned an invalid response."
                )

            if obj_type == "user/full":
                for user in resp.get("user_list", []):
                    sec_uid = user.get("user_info").get("sec_uid")
                    uid = user.get("user_info").get("user_id")
                    username = user.get("user_info").get("unique_id")
                    yield Search.parent.user(
                        sec_uid=sec_uid, user_id=uid, username=username
                    )
                    found += 1

            if obj_type == "general/full":
                for video in resp.get("video_list", []):
                    yield Search.parent.video(
                     # TODO: Fix this
                    )
                    found += 1

            if obj_type == "general/preview":
                for keyword in resp.get("suggestion_list", []):
                    yield Search.parent.keyword_suggestion(
                        keyword=keyword
                    )
                    found += 1

            if not resp.get("has_more", False):
                return

            cursor = resp.get("cursor")
