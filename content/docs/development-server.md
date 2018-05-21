---
$title: Development server
$order: 10.1
$category: Workflow
---
[TOC]

## Using the development server

Grow comes with a built-in development server. The development server dynamically renders and builds pages when requested. This avoids the need to watch files for changes and allows you to iteratively develop without rebuilding your entire site.

You can start the server with the `grow run` command:

```txt
grow run
```

When you start the development server, Grow checks for updates to the SDK, compiles translation catalogs, and runs any preprocessors configured in `podspec.yaml`.

The development server does not currently integrate with any other preprocessing systems, such as Gulp. You must execute those manually.

## Remote access

By default, the development server binds to `localhost` to avoid accidentally providing anyone from accessing your development server. If you need to access the development server from other devices on your local network, use the `--host` and `--port` flags to explicitly set the host and port parameters, respectively.

```txt
grow run --host=0.0.0.0 --port=8080
```

## Web console

The development server includes a basic web console that provides information about your site. Use the console to quickly audit your site's routes, collections, and translations.

Access the console by visiting `http://host:port/_grow`.
