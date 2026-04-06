#!/bin/env python3

"""
**Observability IaC**

This project is a `Pulumi <https://pulumi.com>`_ project that builds resources that allow us to
monitor our various live services and respond to issues. Unlike most of our other Pulumi projects,
this is *not* a `tb_pulumi <https://github.com/thunderbird/pulumi>`_ project as we do not make use
of any of those larger infrastructure patterns.
"""

import pulumi_cloudflare as cloudflare
import tb_pulumi
import tb_pulumi.cloudwatch
import tb_pulumi.fargate
import tb_pulumi.network
import tb_pulumi.secrets

from site24x7 import main as site24x7


project = tb_pulumi.ThunderbirdPulumiProject()
global_config = project.config.get('config', {})
resources = project.config.get('resources', {})

# Some feature flags
build_site24x7 = global_config.get('build_site24x7', False)
build_tbpulumi = global_config.get('build_tbpulumi', False)

if build_site24x7:
    site24x7()

if build_tbpulumi:
    psm_opts = resources.get('tb:secrets:PulumiSecretsManager', {}).get('secrets')
    psm = tb_pulumi.secrets.PulumiSecretsManager(
        name=f'{project.name_prefix}-secrets',
        project=project,
        **psm_opts,
    )

    logdest_opts = resources.get('tb:cloudwatch:LogDestination', {})
    logdests = {
        logdest_name: tb_pulumi.cloudwatch.LogDestination(
            f'{project.name_prefix}-logdest-{logdest_name}',
            project=project,
            **logdest_config,
        )
        for logdest_name, logdest_config in logdest_opts.items()
    }

    vpc_config = resources.get('tb:network:MultiCidrVpc', {}).get('fluentbit', {})
    vpc_fluentbit = tb_pulumi.network.MultiCidrVpc(
        f'{project.name_prefix}-vpc-fluentbit',
        project=project,
        **vpc_config,
    )

    ecs_clusters = {
        cluster_name: tb_pulumi.fargate.AutoscalingFargateCluster(
            f'{project.name_prefix}-fargate-{cluster_name}',
            project=project,
            subnets=vpc_fluentbit.resources.get('subnets', []),
            **cluster_config,
        )
        for cluster_name, cluster_config in resources.get(
            'tb:fargate:AutoscalingFargateCluster'
        ).items()
    }

    # cloudflare_zone_id = project.pulumi_config.require_secret('cloudflare_zone_id')
    # fluent_bit_dns = cloudflare.DnsRecord(
    #     f'{project.name_prefix}-dns-fluentbit',
    #     name='fluent-bit' if project.stack == 'prod' else f'fluent-bit-{project.stack}',
    #     content=ecs_clusters['fluentbit'].resources['load_balancers'],
    #     ttl=60,
    #     type='CNAME',
    #     zone_id=cloudflare_zone_id,
    # )
