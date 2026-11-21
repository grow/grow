---
$title: Live Editor
$order: 5.1
---
## Philosophy

- The Live Editor is a [Grow extension](https://github.com/grow/grow-ext-editor) that creates an interactive content management environment for mangaging Grow projects.
- Pages should be constructed to be compatible with the Live Editor, even if the Live Editor is not being actively used for a project. This ensures that pages will be editable by non-Git users in the future, if that becomes a requirement. 

## Ensure site-wide editor compatibility

- Leverage partials, and the partial loop.
- Partials should be constructed to work in isolation, independent of their position on the page and their relationship with adjacent partials.
- Long-form text content should generally rely on Markdown or HTML documents, and not a list of partials. In other words, do not create a separate partial for every paragraph on a page. This is too complicated to use in practice, and an antipattern.

## Ensure ease of use

Site developers get to choose which options of a partial are exposed in the editor UI to stakeholders. This is done by managing the front matter of a partial.

- Avoid making too many fields editable – "when everything is editable, nothing is."
- Expose "as little as possible, but as much as necessary".
- Partials should expose **just enough** fields to facilitate typical content management flows.
- Typically, strings, images, URLs, and other content/data should be exposed.
- Avoid exposing internal options of a partial in the editor UI.
- Minimize room for error of partial configuration by non-developers.
