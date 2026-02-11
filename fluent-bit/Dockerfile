ARG IMAGE_SUFFIX=""

# The fluent-bit image uses a security-hardened image which does not allow for the traditional
# method of ADDing or COPYing a file into the image straight from disk. You must use an interstitial
# build stage and then copy them in from that build stage.
FROM alpine:latest AS base

# Install our custom files
COPY Dockerfile.filesystem/ /

# Install a hash library from latest tested commit ID, do not pull from master
ADD https://raw.githubusercontent.com/Egor-Skriptunoff/pure_lua_SHA/6adac177c16c3496899f69d220dfb20bc31c03df/sha2.lua \
    /etc/fluent-bit/lua/


# In a separate build stage, copy our files out of the base build into the fluent-bit build
FROM fluent/fluent-bit:4.2.2${IMAGE_SUFFIX:-}

COPY --from=base /fluent-bit /fluent-bit
COPY --from=base /etc/fluent-bit /etc/fluent-bit

# Make sure Lua knows where to find our code
ENV LUA_PATH="/etc/fluent-bit/lua/?.lua;;"

# Set a custom command that refers to our config
ENTRYPOINT [ "/fluent-bit/bin/fluent-bit" ]
CMD [ "-c", "/etc/fluent-bit/fluent-bit.yaml" ]
