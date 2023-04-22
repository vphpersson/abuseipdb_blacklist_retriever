#!/usr/bin/env python

from logging import INFO
from logging.handlers import TimedRotatingFileHandler
from asyncio import run as asyncio_run
from dataclasses import dataclass, field
from argparse import ArgumentParser, FileType

from ecs_tools_py import make_log_handler
from httpx import AsyncClient
from toml import load as toml_load

from abuseipdb_blacklist_retriever import LOG, ABUSEIPDB_BASE_URL, retrieve_blacklist


@dataclass
class Config:
    abuseipdb_api_key: str
    country_codes: list[str]
    geoblock_country_codes: list[str] = field(default_factory=list)
    include_top: bool = False


class AbuseIPDBReporterArgumentParser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **(
                dict(
                    description='Retrieve blacklists from AbuseIPDB.'
                ) | kwargs
            )
        )

        self.add_argument(
            '-c', '--config',
            required=True,
            help='The path of a configuration file.',
            type=FileType(mode='r')
        )


log_handler = make_log_handler(
    base_class=TimedRotatingFileHandler,
    provider_name='abuseipdb_blacklist_retriever',
    generate_field_names=('event.timezone', 'host.name', 'host.hostname')
)(filename='abuseipdb_blacklist_retriever.log', when='W0')

LOG.addHandler(hdlr=log_handler)
LOG.setLevel(level=INFO)


async def main():
    try:
        config = Config(**toml_load(AbuseIPDBReporterArgumentParser().parse_args().config))

        ip_addresses: set[str] = set()

        http_client_options = dict(
            base_url=ABUSEIPDB_BASE_URL,
            headers={
                'Key': config.abuseipdb_api_key
            }
        )
        async with AsyncClient(**http_client_options ) as http_client:
            for country_code in config.country_codes:
                ip_addresses.update(
                    await retrieve_blacklist(
                        http_client=http_client,
                        confidence_minimum=50,
                        only_countries=[country_code]
                    )
                )

            if config.include_top:
                ip_addresses.update(
                    await retrieve_blacklist(
                        http_client=http_client,
                        confidence_minimum=50,
                        except_countries=(config.country_codes + config.geoblock_country_codes)
                    )
                )

        print('\n'.join(ip_addresses))
    except KeyboardInterrupt:
        pass
    except Exception:
        LOG.exception(msg='An unexpected error occurred.')


if __name__ == '__main__':
    asyncio_run(main())
