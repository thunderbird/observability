ARG IMAGE_SUFFIX=""

FROM alpine:latest AS base

# Install our custom files
COPY filesystem/etc/fluent-bit /etc/fluent-bit
COPY filesystem/fluent-bit/ /fluent-bit

FROM fluent/fluent-bit:4.2.2${IMAGE_SUFFIX:-}

COPY --from=base /fluent-bit /fluent-bit
COPY --from=base /etc/fluent-bit /etc/fluent-bit

ENTRYPOINT [ "/fluent-bit/bin/fluent-bit" ]
CMD [ "-c", "/etc/fluent-bit/fluent-bit.yaml" ]
