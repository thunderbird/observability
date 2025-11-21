"""
This library contains helpers to aid with some of the obscurities in Site24x7's API.
"""

import pulumi
import pulumi_site24x7 as site24x7
import requests

from enum import Enum


# This is our default attribute alert group ID. There are many like it, but this one is ours.
ATTRIBUTE_ALERT_GROUP_ID = '217222000000180001'

# Bind easy names to resource classes so as not to complicate the config
MONITOR_TYPES = {
    # There appear to be major problems with the way the Site24x7 Terraform provider (or possibly
    # the transition to a Pulumi provider) handles the JSON matching features in the API. In theory,
    # we should support this, but I can't get around these issues right now.
    # 'API': site24x7.RestApiMonitor,
    'PORT': site24x7.PortMonitor,
    'WEBSITE': site24x7.WebsiteMonitor,
}

# Constants needed for Site24x7 auth and location data gathering
S247_API_URL_BASE = 'https://www.site24x7.com/api'
S247_AUTH_URL_BASE = 'https://accounts.zoho.com'
S247_LOCATION_DATA_FILE = './site24x7-location-data.json'


# Site24x7's API relies upon enumerations of a lot of things. This is not a comprehensive list of
# those things, which you can find at https://www.site24x7.com/help/api/#constants, but it is a list
# of things relevant to our configuration.
class AlertingMode(Enum):
    EMAIL = 1
    SMS = 2
    VOICE = 3
    IM = 4
    TWITTER = 5


class SelectionType(Enum):
    ALL_MONITORS = 0
    MONITOR_GROUPS = 1


class StatusIQRole(Enum):
    SUPER_ADMIN = 21
    ADMIN = 22
    SPOKESPERSON = 23
    BILLING_CONTACT = 24
    READ_ONLY = 25


class UserRole(Enum):
    NO_ACCESS = 0
    SUPER_ADMIN = 1
    ADMIN = 2
    OPERATOR = 3
    BILLING_CONTACT = 4
    SPOKESPERSON = 5
    HOSTING_PROVIDER = 6
    READ_ONLY = 10


def get_site24x7_oauth2_access_token() -> str | pulumi.Output:
    """
    Uses secrets stored in Pulumi's configuration to obtain an access token with which further calls
    to Site24x7's API can be made.
    """

    # Gather secret data
    s247_client_id = pulumi.Config('site24x7').require_secret('oauth2ClientId')
    s247_client_secret = pulumi.Config('site24x7').require_secret('oauth2ClientSecret')
    s247_refresh_token = pulumi.Config('site24x7').require_secret('oauth2RefreshToken')

    def __get_token(client_id, client_secret, refresh_token) -> str:
        """
        Retrieve the access token using the given auth secrets.
        """

        params = {
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
        }
        response = requests.post(f'{S247_AUTH_URL_BASE}/oauth/v2/token', params=params)
        if response.status_code != 200:
            raise RuntimeError(
                'Got an invalid response trying to obtain a Site24x7 access token: '
                f'{response.status_code} {response.reason}'
            )

        return response.json().get('access_token')

    # Wait for these secrets to resolve, then make the auth token API call
    return pulumi.Output.all(
        client_id=s247_client_id, client_secret=s247_client_secret, refresh_token=s247_refresh_token
    ).apply(
        lambda secrets: __get_token(
            client_id=secrets.get('client_id'),
            client_secret=secrets.get('client_secret'),
            refresh_token=secrets.get('refresh_token'),
        )
    )


def get_site24x7_location_data() -> dict | pulumi.Output:
    """
    Retrieve the current set of Site24x7 monitor locations from their API.
    """

    # Get an auth token
    auth_token = get_site24x7_oauth2_access_token()

    def __get_location_data(auth_token) -> dict:
        """
        Get the location data from the API.
        """

        headers = {
            'Accept': 'application/json; version 2.0',
            'Authorization': f'Zoho-oauthtoken {auth_token}',
        }
        response = requests.get(f'{S247_API_URL_BASE}/location_template', headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                "Got an invalid response trying to obtain Site24x7's location data: "
                f'{response.status_code} {response.reason}'
            )

        return response.json().get('data', {})

    return auth_token.apply(lambda auth_token: __get_location_data(auth_token=auth_token))
