import json
import pulumi
import pulumi_site24x7 as site24x7
import site24x7_lib as lib


config = pulumi.Config()


def main():
    # Sometimes we want to update our local copy of Site24x7's obscure location data for reference
    def __write_location_data(location_data):
        try:
            with open(lib.S247_LOCATION_DATA_FILE, 'w') as fh:
                fh.write(json.dumps(location_data, indent=2))
        except IOError:
            raise IOError(f'Could not write location data to file {lib.S247_LOCATION_DATA_FILE}')

    refresh_site24x7_location_data = config.get_bool('refresh_site24x7_location_data')
    if refresh_site24x7_location_data:
        site24x7_location_data = lib.get_site24x7_location_data()
        site24x7_location_data.apply(
            lambda location_data: __write_location_data(location_data=location_data)
        )

    # Build the users
    user_configs = config.get_object('users')
    users = {}

    for user_id, user_config in user_configs.items():
        # We have three special parameters to deal with: selection_type, statusiq_role, user_role.
        # These must correlate to entries in our Enums, which correlate to enumerations in the API.
        selection_type_name = user_config.pop('selection_type').upper()
        selection_type = (
            lib.SelectionType.__members__.get(selection_type_name, '')
            if selection_type_name
            else None
        )
        if selection_type is None:
            raise ValueError(
                f'Invalid selection_type: {selection_type_name} '
                f'Valid values are: {", ".join(lib.SelectionType.__members__.keys())}'
            )

        statusiq_role_name = user_config.pop('statusiq_role', '').upper()
        statusiq_role = (
            lib.StatusIQRole.__members__.get(statusiq_role_name) if statusiq_role_name else None
        )
        if statusiq_role is None:
            raise ValueError(
                f'Invalid statusiq_role: {statusiq_role_name} '
                f'Valid values are: {", ".join(lib.StatusIQRole.__members__.keys())}'
            )

        user_role_name = user_config.pop('user_role', '').upper()
        user_role = lib.UserRole.__members__.get(user_role_name) if user_role_name else None
        if user_role is None:
            raise ValueError(
                f'Invalid user_role: "{user_config["user_role"]}". '
                f'Valid values are: {", ".join(lib.UserRole.__members__.keys())}'
            )

        users[user_id] = site24x7.User(
            f'user-{user_id}',
            critical_notification_media=[lib.AlertingMode.EMAIL.value],
            down_notification_media=[lib.AlertingMode.EMAIL.value],
            notification_media=[lib.AlertingMode.EMAIL.value],
            selection_type=selection_type.value,
            statusiq_role=statusiq_role.value,
            trouble_notification_media=[lib.AlertingMode.EMAIL.value],
            up_notification_media=[lib.AlertingMode.EMAIL.value],
            user_role=user_role.value,
            **user_config,
            opts=pulumi.ResourceOptions(
                ignore_changes=[
                    'notification_media',
                    'down_notification_media',
                    'critical_notification_media',
                    'mobile_settings',
                    'trouble_notification_media',
                    'up_notification_media',
                ],
            ),
        )

    # Create location profiles (collections of locations from which to test your monitors)
    location_profile_configs = config.get_object('location_profiles')
    location_profiles = {}
    for profile_id, profile_config in location_profile_configs.items():
        location_profiles[profile_id] = site24x7.LocationProfile(
            f'locationprofile-{profile_id}',
            **profile_config,
        )

    # Create notification profiles
    notification_profile_configs = config.get_object('notification_profiles')
    notification_profiles = {}
    for profile_id, profile_config in notification_profile_configs.items():
        notification_profiles[profile_id] = site24x7.NotificationProfile(
            f'notificationprofile-{profile_id}',
            **profile_config,
        )

    # We call these "user groups" because that's what the TF calls them. The web console calls them
    # "user alert groups", though.
    user_group_configs = config.get_object('user_groups')
    user_groups = {
        user_group_id: site24x7.UserGroup(
            f'usergroup-{user_group_id}',
            attribute_group_id=lib.ATTRIBUTE_ALERT_GROUP_ID,
            display_name=user_group_config.get('display_name'),
            users=[users[user_id].id for user_id in user_group_config.get('users')],
            opts=pulumi.ResourceOptions(depends_on=[*users.values()]),
        )
        for user_group_id, user_group_config in user_group_configs.items()
    }

    # Create monitoring groups to organize monitors into
    monitor_group_configs = config.get_object('monitor_groups')
    monitor_groups = {}
    for monitor_group_id, monitor_group_config in monitor_group_configs.items():
        user_group_ids = monitor_group_config.pop('user_groups', [])
        monitor_groups[monitor_group_id] = site24x7.MonitorGroup(
            f'monitorgroup-{monitor_group_id}',
            user_group_ids=[user_groups[user_group_id].id for user_group_id in user_group_ids],
            **monitor_group_config,
            opts=pulumi.ResourceOptions(depends_on=[*user_groups.values()]),
        )

    # Create the monitors themselves, after the monitor groups get applied
    def __create_monitors(all_monitor_groups, all_notification_profiles, all_user_groups):
        """
        Create the monitors defined in our configurations, resolving the names of monitoring and
        user groups into the IDs given to them by Site24x7.
        """

        monitors = {}
        for monitor_id, monitor_config in config.get_object('monitors').items():
            # Pop the "kind" option out of the config and pull the actual class it refers to
            kind = lib.MONITOR_TYPES.get(monitor_config.pop('kind', '').upper())

            # Error if we don't get a valid kind
            if not kind:
                raise ValueError(
                    f'Config for monitor {monitor_id} does not have a valid "kind" value. '
                    f'Valid values are: {lib.MONITOR_TYPES.keys()}'
                )

            # Pop the "location_profile" option, replacing it with the correct name. This allows us
            # to change the name of a location profile without having to change every reference.
            location_profile = monitor_config.pop('location_profile', None)
            if location_profile:
                location_profile_name = location_profile_configs.get(location_profile, {}).get(
                    'profile_name'
                )
                if not location_profile_name:
                    raise ValueError(
                        f'Monitor {monitor_id} was given an invalid location_profile: '
                        f'"{location_profile}"'
                    )
                monitor_config['location_profile_name'] = location_profile_name

            # Convert monitor group names into their correct IDs, allowing us to refer to these by
            # the name we give them in the config and not the obscure numerical ID given by
            # Site24x7's API.
            monitor_config['monitor_groups'] = [
                all_monitor_groups[monitor_group]
                for monitor_group in monitor_config.get('monitor_groups', {})
            ]

            # Convert user group names into IDs, remove the user_groups key from the config
            monitor_config['user_group_ids'] = [
                all_user_groups[user_group] for user_group in monitor_config.get('user_groups', {})
            ]
            monitor_config.pop('user_groups', None)

            # Convert notification profile names into IDs
            notification_profile_name = monitor_config.pop('notification_profile', None)
            if not notification_profile_name:
                raise ValueError(f'No notification_profile was provided for monitor {monitor_id}.')

            notification_profile_id = all_notification_profiles.get(notification_profile_name)
            if not notification_profile_id:
                raise ValueError(
                    f'Invalid notification profile name "{notification_profile_name} '
                    f'provided for monitor {monitor_id}.'
                )
            monitor_config['notification_profile_id'] = str(notification_profile_id)

            # Create the monitor, arbitrarily passing other config options through
            monitors[monitor_id] = kind(
                f'monitor-{monitor_id}',
                **monitor_config,
                opts=pulumi.ResourceOptions(
                    depends_on=[
                        *location_profiles.values(),
                        *monitor_groups.values(),
                        *notification_profiles.values(),
                        *user_groups.values(),
                    ]
                ),
            )

    # We need all monitor groups, notification groups, and user groups to be fully resolved so we
    # can grab their API-assigned IDs. Here we collect all of these outputs and then create a
    # compound output that we then resolve before actually creating these monitors.
    monitor_group_ids = {
        monitor_group_id: monitor_group.id
        for monitor_group_id, monitor_group in monitor_groups.items()
    }
    notification_profile_ids = {
        notification_profile_id: notification_profile.id
        for notification_profile_id, notification_profile in notification_profiles.items()
    }
    user_group_ids = {
        user_group_id: user_group.id for user_group_id, user_group in user_groups.items()
    }
    pulumi.Output.all(
        monitor_group_ids=monitor_group_ids,
        notification_profile_ids=notification_profile_ids,
        user_group_ids=user_group_ids,
    ).apply(
        lambda outputs: __create_monitors(
            all_monitor_groups=outputs['monitor_group_ids'],
            all_notification_profiles=outputs['notification_profile_ids'],
            all_user_groups=outputs['user_group_ids'],
        )
    )
