FROM fluent/fluent-bit:4.2.2-debug
# FROM fluent/fluent-bit:4.2.2

WORKDIR /fluent-bit

# Delete the default config entirely and set up our custom directories
RUN rm -rf etc

# Install our custom files
COPY filesystem/ /

ENTRYPOINT [ "/fluent-bit/bin/fluent-bit" ]
CMD [ "-c", "/fluent-bit/etc/fluent-bit.yaml" ]