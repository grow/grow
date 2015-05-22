---
$title: Development server
$order: 0
$category: Workflow
---
# Development server

[TOC]

## Run Command
Grow ships with a built-in development server to test your changes locally, which you can start using the run command:

    grow run /path/to/project


## Real Time Preview
When you start the development server, Grow checks for updates to the SDK, tests your pod, compiles translations, and runs preprocessors. If any of these tasks fail, the test server will fail to start. Here's what it looks like when you start your development server:

    Checking for updates to the Grow SDK...
    Your Grow SDK is the latest version: 0.X.X
    Compiled /source/sass/main.sass -> /static/css/main.min.css
    Serving pod /Users/me/git/growsdk.org => http://localhost:8080

Your development server is now running, and by default, your web browser will open to your project's root, ready for you to preview.

Changes to content (in content), templates (in views), or static files are immediately reflected, and a quick refresh of any page allows you to see your changes immediately.

Grow watches for changes to files that require preprocessing (such as files in source or translations). Changes to those files will cause Grow to kick off a preprocessor to build the generated files, and your changes will be reflected in the live preview almost immediately.
