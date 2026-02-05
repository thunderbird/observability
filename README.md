# Thunderbird Observability

**Observability information for TBPro.**

This repo contains information about Thunderbird's specific implementation of our other repos' infrastructure and applications. Here we:

- Document implementation details for transparency and engineer onboarding purposes.
- Build observability resources such as Site24x7 users and monitors.

[!IMPORTANT]
This repo is a work in progress. You may encounter inaccurate or incomplete information. Please be patient as we get this project underway.


## Incident Response


### Root Cause Analyses

When an incident occurs, perform a root cause analysis (RCA). Create a directory path in the [`rcas`](./rcas) directory corresponding to
the date of the incident, then copy the `template.md` file there. The filename should include the date and a title for the incident. Fill
the copied template out as you perform the analysis.

