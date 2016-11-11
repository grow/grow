---
$title: UI Tools
$category: Reference
$order: 10
---
# UI Tools

[TOC]

Grow's development server comes with the ability to add tools that expand the development experience.

## Tools

Many tools can be found and installed using [NPM](https://www.npmjs.com/search?q=grow-tool) by looking for the `grow-tool-` prefix.

Some examples include:

  - [grow-tool-analytics-highlight](https://www.npmjs.com/package/grow-tool-analytics-highlight) Highlights automatically tracked analytics that use data attributes (ex: [autotrack](https://github.com/googleanalytics/autotrack)).
  - [grow-tool-image-swap](https://www.npmjs.com/package/grow-tool-image-swap) Allows dragging new image files to temporarily replace images to preview without changing the source.

### Installing

For basic installations:

Add the tool to the project's `package.json` dev dependencies:

[sourcecode:json]
"devDependencies": {
  "grow-tool-analytics-highlight": "^0.0.5"
}
[/sourcecode]

Run `grow install` to install the new dependency.

Update the `podspec.yaml` to enable the new tool:

[sourcecode:yaml]
ui:
  tools:
  - kind: analytics-highlight
    options:
      prefix: event
[/sourcecode]

### CDNs and Local Sources

Tools can also be hosted on third party systems such as CDNs or custom within the project:

[sourcecode:yaml]
ui:
  tools:
  - kind: analytics-highlight
    paths:
      script: https://some.cdn.com/grow/ui/tool.js
      style: https://some.cdn.com/grow/ui/tool.css
[/sourcecode]

## Custom Tools

There is an basic example project for creating custom tools:
[grow-tool-template](https://github.com/grow/grow-tool-template).
