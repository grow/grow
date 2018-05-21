---
$title: Create Extensions
$category: Extensions
$order: 5.2
---
[TOC]

Grow has a powerful extension system that enables you to extend the
functionality of Grow with extensions.

### Example Extension

As an example of a simple Grow extension see the [html min extension][html_min].

### Anatomy of an Extension

Grow extensions work by creating hooks to bind to events that happen within
Grow. For example, a hook to change the contents of a page after it has already
been rendered. Each extension can bind to any number of hooks.

Extensions are provided with a configuration optionally defined in the
`podspec.yaml` that can be used to control the extension's functionality:

```yaml
# podspec.yaml
ext:
- extensions.html_min.HtmlMinExtension:
    options:
      remove_comments: true
      reduce_boolean_attributes: false
```

For complex extensions specific hooks can be enabled or disabled piecemeal:

```yaml
# podspec.yaml
ext:
- extensions.complex.ComplexExtension:
    enabled:
    - post_render
    disabled:
    - dev_file_change
```

### Extension Hooks

Base hooks are defined by Grow and can be extended in the extension. When hooks
are triggered in Grow (ex: after the content is rendered) it calls the `trigger`
method on the hook.

 Hook triggers follow some basic conventions:

  - The first argument is the `previous_result` from any hooks already triggered.
  - Arguments change depending on the hook and are documented below.
  - Each trigger method should have `*_args, **_kwargs` as the last two
  arguments.

For hooks that are expecting a specific result a result object will be provided
in the `previous_result` argument and should just be updated as needed. If there
is a specific return type it will be documented with the hook.

Even if your extension doesn't change the `previous_result`, the
`previous_result` should be returned to continue the chain of extensions.

By using the `*_args, **_kwargs` on all trigger methods it allows Grow to add
additional arguments to the hook without breaking existing extensions.

```py
from grow.extensions import hooks


class MyPostRenderHook(hooks.PostRenderHook):
    """Handle the post-render hook."""

    def trigger(self, previous_result, doc, raw_content, *_args, **_kwargs):
        """Execute post-render modification."""
        content = previous_result if previous_result else raw_content

        # Do something to modify the contents.

        return content
```

### Extensions

A simple extension only needs to extend the `BaseExtension` and define the
`available_hooks` property.

```py
from grow import extensions


class MyExtension(extensions.BaseExtension):
    """Example Extension."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [MyPostRenderHook]
```

For special cases when you need to have additional arguments to the hook class
you can create hook getters in the extension to control how the hook is created.

```py
from grow import extensions


class MyExtension(extensions.BaseExtension):
  """Example Extension."""

  @property
  def available_hooks(self):
    """Returns the available hook classes."""
    return [MyPostRenderHook]

  def post_render_hook(self):
    """Returns the hook object."""
    return MyPostRenderHook(self, other_arg=True)
```

### Grow Hooks

The following hooks are currently available for extensions.

### hooks.DevFileChangeHook

When a file is changed when running the development server this hook is
triggered.

```py
def trigger(self, previous_result, pod_path, *_args, **_kwargs):
  return previous_result
```

 - `pod_path` – path of the file that changed in the pod.

See the [core routes extension][core_routes] for an example of the dev file change.

### hooks.DevHandlerHook

When running the local development server the dev handler hook allows for
adding custom handlers for the development server.

```py
def trigger(self, previous_result, routes, *_args, **_kwargs):
  return previous_result
```

 - `routes` - The routes object for adding the handler.

See the [core routes extension][core_routes] for an example of the dev handler.

### hooks.PostRenderHook

```py
def trigger(self, previous_result, doc, raw_content, *_args, **_kwargs):
  return previous_result
```

 - `doc` – The document being rendered. This can be a normal document or a
   static document.
 - `raw_content` – The raw rendered content.

 See the [html min extension][html_min_src] for an example of the dev handler.

[core_routes]: https://github.com/grow/grow/blob/master/grow/extensions/core/routes_extension.py
[html_min]: https://github.com/grow/grow-ext-html-min
[html_min_src]: https://github.com/grow/grow-ext-html-min/blob/master/html_min/html_min.py
