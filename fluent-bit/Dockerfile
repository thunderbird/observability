ARG IMAGE_SUFFIX=""

# The fluent-bit image uses a security-hardened image which does not allow for the traditional
# method of ADDing or COPYing a file into the image straight from disk. You must use an interstitial
# build stage and then copy them in from that build stage.
FROM alpine:latest AS base

# Install our custom files
COPY filesystem/etc/fluent-bit /etc/fluent-bit
COPY filesystem/fluent-bit/ /fluent-bit


# In a separate build stage, copy our files out of the base build into the fluent-bit build
FROM fluent/fluent-bit:4.2.2${IMAGE_SUFFIX:-}

COPY --from=base /fluent-bit /fluent-bit
COPY --from=base /etc/fluent-bit /etc/fluent-bit

# Set a custom command that refers to our config
ENTRYPOINT [ "/fluent-bit/bin/fluent-bit" ]
CMD [ "-c", "/etc/fluent-bit/fluent-bit.yaml" ]
