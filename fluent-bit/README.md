# fluent-bit

[Fluentd](https://www.fluentd.org/) is an open source program that recieves data from any number of sources through a variety of ingestion mechanisms, then processes that data and emits it back out to other destinations. This is commonly used to collect and ship observability data like metrics and logs.

[Fluent-bit](https://fluentbit.io/) was originally designed to solve the same problems as fluentd, but on a microcontroller's scale. It is incredibly fast and lightweight, even more so than fluentd, which is itself very fast and lightweight. This comes at some cost, primarily that you cannot use the Ruby language to manipulate data. Since this is no great loss, we opt for the flyweight option.

The contents of this directory contain all the elements we need to build and locally test fluent-bit for our environments. For live environment installations, see the [`pulumi`](../pulumi/) directory.


## What do we use it for?

Today, we use this to receive metrics from Stalwart and convert them into Posthog-compatible payloads, allowing us to live-import key Stalwart observability data into a central location.


## What else can we use it for?

fluent-bit is commonly used for metrics and log aggregation. If you need to ship a custom metric, preserve log files, or centralize other data in Posthog or some other platform we can ship to, please consider adding it to this installation.


## Usage

fluent-bit provides two Docker images for each version they release. One, intended for actual deployments, is security-hardened and contains no shell or useful administrative tools. The other is a debug image which you can inspect directly. We customize both Docker images by embedding our custom configurations into them and wrapping them in a handy docker-compose configuration.


### Dotenv File

Before you begin, make a copy of the provided `.env.example` file:

```bash
cp .env.example .env
```

Edit that file and ensure all the values are correct for your development needs.


### Build images

To build the deployable image, you can use the standard build command:

```bash
docker build .
```

Or you can use compose:

```bash
docker-compose build

# or

docker-compose build fluent-bit
```

To build the debug image, you can specify a build arg:

```bash
docker build --build-arg IMAGE_SUFFIX="-debug" .
```

Or, again, use compose:

```bash
docker-compose build fluent-bit-debug
```


### Running fluent-bit locally

Run the production image:

```bash
docker-compose up --build
```

Run the debug image in the foreground, leaving you in a live shell:

```bash
docker-compose run --build fluent-bit-debug
```


### Testing events

Make any alterations you need to test. Run fluent-bit using one of the above methods. Craft a custom payload (here we assume that's in `payload.json`) and ship it with `curl`:

```bash
echo '{"foo": "bar"}' > payload.json
curl -i \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '@payload.json' \
    http://localhost:1337/your/tag
```