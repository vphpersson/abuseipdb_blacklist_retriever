from logging import getLogger, Logger
from typing import Final, Sequence

from httpx import AsyncClient, Response

LOG: Final[Logger] = getLogger(__name__)

ABUSEIPDB_BASE_URL: Final[str] = 'https://api.abuseipdb.com'

_ENTRIES_LIMIT: Final[int] = 500_000


async def retrieve_blacklist(
    http_client: AsyncClient,
    confidence_minimum: int | None = None,
    only_countries: Sequence[str] | None = None,
    except_countries: Sequence[str] | None = None
) -> list[str]:
    """
    Retrieve a blacklist from AbuseIPDB.

    :param http_client: An HTTP client with which to perform the retrieval.
    :param confidence_minimum:
    :param only_countries:
    :param except_countries:
    :return: A list of IP addresses.
    """

    params = dict(limit=_ENTRIES_LIMIT)

    if confidence_minimum:
        params['confidenceMinimum'] = confidence_minimum

    if only_countries:
        params['onlyCountries'] = ','.join(only_countries)

    if except_countries:
        params['exceptCountries'] = ','.join(except_countries)

    blacklist_response: Response = await http_client.get(
        url='/api/v2/blacklist',
        headers={'Accept': 'text/plain'},
        params=params
    )
    blacklist_response.raise_for_status()

    return blacklist_response.text.splitlines()




