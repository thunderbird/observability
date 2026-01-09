# January 06, 2026: Stalwart TLS Certificate Expiration


## Facts

**Impacted Services:** The following services in the stage environment:

- Accounts
- Appointment
- Mail
- Send

**Incident Began:** January 06, 2026 @ 14:32 UTC

**Incident Resolved:** January 06, 2026 @ 18:27 UTC

**Total Incident Time:** 3 hours, 55 minutes


## Overview

At 14:32 UTC on January 06, 2026, the Stalwart instances in stage attempted to renew their ACME-provided TLS certificates. This process reported completing successfully, but the resulting certificate failed signature validation. All Stalwart services began presenting invalid certificate data. To resolve this, we disabled ACME as a TLS certificate provider altogether, opting instead for a certificate managed by AWS. This will still need to be renewed periodically, so we have configured monitors to alert when the certificate is within 30 days of expiration.


## Quick Reference

- [New Issue: Remove `verify=False` from Stalwart client](https://github.com/thunderbird/thunderbird-accounts/issues/494)
- [New Issue: Remove the Accounts API health check call to Stalwart API](https://github.com/thunderbird/thunderbird-accounts/issues/495)
- [New Issue: Change `PATCH` call to `GET`](https://github.com/thunderbird/thunderbird-accounts/issues/496)
- [New Issue: Document service dependencies](https://github.com/thunderbird/private-issue-tracking/issues/26)
- [New Issue: Document a runbook for common issues](https://github.com/thunderbird/private-issue-tracking/issues/27)


## Timeline

*All times below are listed in UTC and occurred on January 06, 2026.*

- **14:32** - The `mailstrom-stalwart-stage-50` instance (the private admin instance for the stage environment) starts processing an ACME renewal. This process involves Stalwart using a CloudFront API token to adjust DNS records in the `stage-thundermail.com` domain to satisfy a challenge to the certificate issuer proving we own the domain. This appears to go well. The process completes with explicit success messages indicating a new expiration date in April.

- **14:33** - Calls that are made from Accounts API to the Stalwart API begin to fail SSL validation. This is a "bad signature" error. Later, manual inspection of the certificate Stalwart is now presenting will confirm that the cert is present and formatted correctly, but failing signature validation. This error manifests as a 500 error every time the `/health` endpoint is called. That happens every 30 seconds from the load balancer.

- **14:34** - The load balancer's target group has seen enough of these 500 errors to start considering the Accounts API to be offline. ECS responds by trying to cycle the Accounts containers. They will not come online and enter load balancer rotation as long as Stalwart is unable to provide a valid certificate.

- **14:38** - Site24x7, our primary external monitoring service, reports that the Accounts Backend is down from all locations. This is the stage environment, so admins are notified by email, not by push notification or urgent phone call.

- **16:15** - Thunderbird engineering staff comes online for the day and begins to take notice. Thunderbird Desktop throws errors saying that the certificate has changed when trying to sync mail. When attempting to override the old cert with the new, the new cert's validation fails. Investigation begins.

- **17:35** - The problem is identified as being related to the refresh of an ACME certificate in Stalwart. We had repaired this problem in the production environment on November 7, 2026 in response to the same type of incident, but did not retrofit the stage environment to the same configuration. The solution is devised: Create a new certificate in AWS Certificate Manager. Export it and pull the cert data into Stalwart. Disable ACME altogether, using the ACM cert for all functions by default.

- **18:27** - The new configuration is in place and all the stage servers are in sync. The accounts backend is now able to communicate with the Stalwart API once more, so those containers stabilize. Service is restored.



## Evidence and Investigations


### Stalwart successfully processes an ACME cert renewal

The following is a snippet of logs taken from the `mailstrom-stalwart-stage-50` instance, which is the admin instance for the stage deployment.

```
Jan 06 14:32:45 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:32:45Z INFO ACME order started (acme.order-start) hostname = ["*.stage-thundermail.com"]
Jan 06 14:32:48 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:32:48Z INFO ACME authentication started (acme.auth-start) hostname = "stage-thundermail.com", type = "dns-01", id = "letsencrypt"
Jan 06 14:32:58 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:32:58Z INFO ACME authentication started (acme.auth-start) hostname = "stage-thundermail.com", type = "dns-01", id = "letsencrypt"
Jan 06 14:33:02 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:02Z INFO ACME DNS record created (acme.dns-record-created) hostname = "_acme-challenge.stage-thundermail.com", details = "stage-thundermail.com", id = "letsencrypt"
Jan 06 14:33:02 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:02Z INFO ACME DNS record propagated (acme.dns-record-propagated) id = "letsencrypt", hostname = "_acme-challenge.stage-thundermail.com", details = "stage-thundermail.com"
Jan 06 14:33:05 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:05Z INFO ACME authentication valid (acme.auth-valid) hostname = "stage-thundermail.com", id = "letsencrypt"
Jan 06 14:33:05 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:05Z INFO ACME authentication completed (acme.auth-completed) id = "letsencrypt", hostname = ["*.stage-thundermail.com"]
Jan 06 14:33:06 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:06Z INFO ACME order ready (acme.order-ready) id = "letsencrypt", hostname = ["*.stage-thundermail.com"]
Jan 06 14:33:07 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:07Z INFO ACME order valid (acme.order-valid) id = "letsencrypt", hostname = ["*.stage-thundermail.com"]
Jan 06 14:33:08 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:08Z INFO Processing ACME certificate (acme.process-cert) id = "letsencrypt", hostname = ["*.stage-thundermail.com"], validFrom = 2026-01-06T13:34:37Z, validTo = 2026-04-06T13:34:36Z, due = 2026-03-07T13:34:36Z
Jan 06 14:33:08 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:08Z INFO ACME order completed (acme.order-completed) domain = ["*.stage-thundermail.com"], expires = 2026-03-07T13:34:35Z
Jan 06 14:33:27 ip-10-1-100-101.eu-central-1.compute.internal docker[11756]: 2026-01-06T14:33:27Z INFO Processing ACME certificate (acme.process-cert) id = "letsencrypt", hostname = ["*.stage-thundermail.com"], validFrom = 2026-01-06T13:34:37Z, validTo
 = 2026-04-06T13:34:36Z, due = 2026-03-07T13:34:36Z

```

The issue here is that the messaging reads like success, when we know that something actually failed. We have engaged the developers of Stalwart to see if this issue is familiar, but as we have little detailed info on this (and nothing popped out when searching the issues list), it is unlikely that we will receive a highly detailed explanation.

This occured on an older version of the server at a time when we need to upgrade multiple versions very soon. Since we have moved away from this usage model entirely, there seems little value in reproducing the behavior (doing so with increased logging would be the logical next diagnostic step). We may never get an answer to this particular mystery. 


### Accounts API throws errors about Stalwart's API certificate

Beginning at 14:33, we can see actual cert validation errors appear associated with failed health checks against Accounts API. This health check makes calls to various backend services (the database, cache, etc.) to validate that they're online. There isn't any special logic here, just a [call to `get_telemetry()`](https://github.com/thunderbird/thunderbird-accounts/blob/878f405980ae572dd9100271843f269137776bf0/src/thunderbird_accounts/infra/views.py#L43-L51) that ultimately makes a [`PATCH` call to Stalwart's `/telemetry/metrics`](https://github.com/thunderbird/thunderbird-accounts/blob/878f405980ae572dd9100271843f269137776bf0/src/thunderbird_accounts/mail/clients.py#L188) Suddenly, we see errors like this:

```
[DEBUG] 2026-01-06 14:33:34,347: Starting new HTTPS connection (1): auth-stage.tb.pro:443
requests.exceptions.SSLError: HTTPSConnectionPool(host='mailstrom-stage-management-i.stage-thundermail.com', port=8080): Max retries exceeded with url: /api/telemetry/metrics (Caused by SSLError(SSLError(1, '[SSL: BAD_SIGNATURE] bad signature (_ssl.c:1032)')))
raise SSLError(e, request=request)
File "/app/.venv/lib/python3.13/site-packages/requests/adapters.py", line 675, in send
r = adapter.send(request, **kwargs)
File "/app/.venv/lib/python3.13/site-packages/requests/sessions.py", line 703, in send
resp = self.send(prep, **send_kwargs)
File "/app/.venv/lib/python3.13/site-packages/requests/sessions.py", line 589, in request
~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
return session.request(method=method, url=url, **kwargs)
File "/app/.venv/lib/python3.13/site-packages/requests/api.py", line 59, in request
return request("patch", url, data=data, **kwargs)
File "/app/.venv/lib/python3.13/site-packages/requests/api.py", line 145, in patch
response = requests.patch(f'{self.api_url}/telemetry/metrics', headers=self.authorized_headers, verify=False)
File "/app/src/thunderbird_accounts/mail/clients.py", line 188, in get_telemetry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
stalwart_client.get_telemetry()
File "/app/src/thunderbird_accounts/infra/views.py", line 48, in __check_stalwart
result = self.func(*args, **kwargs)
File "/app/src/thunderbird_accounts/infra/views.py", line 22, in __call__
~~~~~~~~~~~~~~~~^^
stalwart_health, stalwart_duration = __check_stalwart()
File "/app/src/thunderbird_accounts/infra/views.py", line 75, in health_check
return callback(request, *args, **kwargs)
File "/app/.venv/lib/python3.13/site-packages/sentry_sdk/integrations/django/views.py", line 94, in sentry_wrapped_callback
return func(*args, **kwargs)
File "/app/.venv/lib/python3.13/site-packages/asgiref/sync.py", line 493, in thread_handler
result = self.fn(*self.args, **self.kwargs)
File "/app/.venv/lib/python3.13/site-packages/asgiref/current_thread_executor.py", line 40, in run
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ret = await asyncio.shield(exec_coro)
File "/app/.venv/lib/python3.13/site-packages/asgiref/sync.py", line 439, in __call__
^
)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
request, *callback_args, **callback_kwargs
^^^^^^^^^^^^^^^^^^^^^^^
response = await wrapped_callback(
File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/base.py", line 253, in _get_response_async
raise exc_info[1]
File "/app/.venv/lib/python3.13/site-packages/asgiref/sync.py", line 489, in thread_handler
^^^^^^^^^^^^^^^^^^^^^^^^^^^
response = await get_response(request)
File "/app/.venv/lib/python3.13/site-packages/django/core/handlers/exception.py", line 42, in inner
raise exc_info[1]
File "/app/.venv/lib/python3.13/site-packages/asgiref/sync.py", line 489, in thread_handler
Traceback (most recent call last):
During handling of the above exception, another exception occurred:
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='mailstrom-stage-management-i.stage-thundermail.com', port=8080): Max retries exceeded with url: /api/telemetry/metrics (Caused by SSLError(SSLError(1, '[SSL: BAD_SIGNATURE] bad signature (_ssl.c:1032)')))
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
raise MaxRetryError(_pool, url, reason) from reason # type: ignore[arg-type]
File "/app/.venv/lib/python3.13/site-packages/urllib3/util/retry.py", line 519, in increment
)
method, url, error=new_e, _pool=self, _stacktrace=sys.exc_info()[2]
retries = retries.increment(
File "/app/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 841, in urlopen
)
chunked=chunked,
...<9 lines>...
method=request.method,
resp = conn.urlopen(
File "/app/.venv/lib/python3.13/site-packages/requests/adapters.py", line 644, in send
Traceback (most recent call last):
The above exception was the direct cause of the following exception:
urllib3.exceptions.SSLError: [SSL: BAD_SIGNATURE] bad signature (_ssl.c:1032)
raise new_e
File "/app/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 488, in _make_request
)
**response_kw,
...<10 lines>...
conn,
response = self._make_request(
File "/app/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 787, in urlopen
Traceback (most recent call last):
During handling of the above exception, another exception occurred:
ssl.SSLError: [SSL: BAD_SIGNATURE] bad signature (_ssl.c:1032)
~~~~~~~~~~~~~~~~~~~~~~~~~^^
self._sslobj.do_handshake()
File "/usr/local/lib/python3.13/ssl.py", line 1372, in do_handshake
~~~~~~~~~~~~~~~~~^^
self.do_handshake()
File "/usr/local/lib/python3.13/ssl.py", line 1076, in _create
^
)
^^^^^^^^^^^^^^^
session=session
...<5 lines>...
^^^^^^^^^^
sock=sock,
~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
return self.sslsocket_class._create(
File "/usr/local/lib/python3.13/ssl.py", line 455, in wrap_socket
~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
return ssl_context.wrap_socket(sock, server_hostname=server_hostname)
File "/app/.venv/lib/python3.13/site-packages/urllib3/util/ssl_.py", line 524, in _ssl_wrap_socket_impl
ssl_sock = _ssl_wrap_socket_impl(sock, context, tls_in_tls, server_hostname)
File "/app/.venv/lib/python3.13/site-packages/urllib3/util/ssl_.py", line 480, in ssl_wrap_socket
)
tls_in_tls=tls_in_tls,
...<8 lines>...
sock=sock,
ssl_sock = ssl_wrap_socket(
File "/app/.venv/lib/python3.13/site-packages/urllib3/connection.py", line 969, in _ssl_wrap_socket_and_match_hostname
)
assert_fingerprint=self.assert_fingerprint,
...<14 lines>...
sock=sock,
sock_and_verified = _ssl_wrap_socket_and_match_hostname(
File "/app/.venv/lib/python3.13/site-packages/urllib3/connection.py", line 790, in connect
~~~~~~~~~~~~^^
conn.connect()
File "/app/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 1093, in _validate_conn
~~~~~~~~~~~~~~~~~~~^^^^^^
self._validate_conn(conn)
File "/app/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py", line 464, in _make_request
Traceback (most recent call last):
[ERROR] 2026-01-06 14:33:34,395: Internal Server Error: /health
INFO: 10.11.47.189:3488 - "GET /health HTTP/1.1" 500 Internal Server Error
```

This is the clearest presentation of this problem in our view.

It also raises a question: Why is the method of this call a `PATCH`? It appears this is an undocumented [endpoint](https://stalw.art/docs/api/management/endpoints/) and that we should be making a `GET` call instead. We have opened [an investigative issue](https://github.com/thunderbird/thunderbird-accounts/issues/496) to track this.



### Accounts API makes insecure requests to Stalwart API

While browsing logs related to this incident, we noticed a separate issue. Even under normal operation, we see this type of message in the Accounts API logs repeatedly:

```
/app/.venv/lib/python3.13/site-packages/urllib3/connectionpool.py:1097: InsecureRequestWarning: Unverified HTTPS request is being made to host 'mailstrom-stage-management-i.stage-thundermail.com'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
```

The Accounts API contains a [partial Stalwart API client](https://github.com/thunderbird/thunderbird-accounts/blob/878f405980ae572dd9100271843f269137776bf0/src/thunderbird_accounts/mail/clients.py#L38). This allows some basic CRUD operations on [Stalwart principals](https://stalw.art/docs/auth/principals/overview/) that let us manage domains and user accounts there, and it exposes the telemetry endpoint for health check usage. Throughout this client, requests are made to the Stalwart API using the Python `requests` library with `verify=False` set. This allows for things like self-signed certs in testing/development environments.

However, we should investigate the ability to turn this off. At this point, all of our environments should be using fully validated certificates, and SSL validation should always pass. We can probably remove these options, and we should, or else we should identify what other changes need to happen in order for us to remove them. I've created an issue for this [here](https://github.com/thunderbird/thunderbird-accounts/issues/494).


### Specific relationships between accounts-related services

The product known in broad terms as "Thunderbird Accounts" consists of two primary components: the Accounts API (which is a Django installation presenting the API and a small frontend) and a [Keycloak](https://www.keycloak.org/) installation. These are tightly coupled with the Stalwart installation which is considered part of the "Thundermail" project.

The Accounts API has a number of dependencies on the Stalwart API, mostly around managing accounts and domains in Stalwart via changes made in the Accounts service. One outlier of sorts is in the health check. We make a `PATCH` call for telemetry data as a method of verifying that Stalwart is alive. This is the source of the flailing Accounts API containers: the call failed at the SSL handshake level and an uncaught exception threw `500` errors back at the load balancer's health checks.

If we wanted to prevent this, we would either need to catch this exception (and presumably other exceptions we haven't encountered yet from incidents that haven't happened yet) and do something other than throw a 500, **or** we would need to remove this call from the health check entirely. To make this call, we need to investigate the impact of a Stalwart API outage.

All of our services — Stalwart, Accounts, Appointment, and Send alike — have an OIDC integration with Keycloak for token validation. Therefore, if Keycloak is offline, normal authentication will fail across the board. This makes perfect sense since Keycloak should be the actual source of truth for user identity.

Keycloak itself does not have any dependencies upon either Stalwart or Accounts. In a bootstrapping situation, it is Keycloak which must come online first in order for the other services to become stable. Since Accounts makes these calls in its health check, that means that Stalwart must be next to come online, and that Accounts itself must come online last. If we remove the health check dependency on Stalwart, this would remove this hard service dependency.

Keycloak shows no signs of malfunction during the incident, though, which also makes sense given this dependency model. Its request rate is extremely consistent, the target group reports no 500-class errors at all, and the Keycloak service logs report absolutely nothing interesting.

There is no reason to think that this Accounts outage impacted other Pro Services. In that light, we may consider that a Stalwart API outage *does* constitute or justify a full Accounts outage.

We will continue to discuss this topic in [this issue created for that purpose](https://github.com/thunderbird/thunderbird-accounts/issues/495).

We have also [created a task](https://github.com/thunderbird/private-issue-tracking/issues/26) to document the full set of service dependencies and [another task](https://github.com/thunderbird/private-issue-tracking/issues/27) to begin documenting runbook entries for incidents like this.