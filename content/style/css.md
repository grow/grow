---
$title: CSS
$order: 3
---
## Directory structure

```text
├── podspec.yaml
├── source/
|   ├── sass/
|   |   ├── mixins/
|   |   |   ├── _breakpoints.sass
|   |   |   ├── _type.sass
|   |   |   ├── ...
|   |   ├── macros/
|   |   |   ├── _<macro>.sass
|   |   |   ├── ...
|   |   ├── partials/
|   |   |   ├── _<partial>.sass
|   |   |   ├── ...
|   |   ├── vendor/
|   |   |   ├── ...
|   |   ├── _base.sass
|   |   ├── _vars.sass
|   |   ├── ...
|   |   └── main.sass
```

## Naming conventions

- Use URL-style casing (lowercase, hyphen-delimited) for files, variables, functions, animations, mixins, etc.
- Avoid using underscores or camel case to separate words.
- Avoid prefixing with your project name, unless your website is specifically required to embed within a dirty CSS space.

## Use BEM

- Use BEM, and follow it strictly.
- Avoid styling IDs.
- Avoid styling HTML elements (use `div` over semantic elements).*

*This may negatively impact accessibility. To build an accessible site
with this approach, make sure to use the proper `aria` and `role` attributes
on elements.

## Class names should follow content structure

- BEM names should correspond directly to the partial and its structure.
- File names should be consistent with the view (the partial and/or the macro).
- There should be one CSS (Sass) file per partial template.

<figcaption>/content/partials/foo.yaml</figcaption>
```yaml
partial: foo
title: My title.
body: My body.
```

<figcaption>/views/partials/foo.html</figcaption>
```jinja
<div class="foo {{partial.class}}">
  <div class="foo__title">{{partial.title}}</div>
  <div class="foo__body">{{partial.body}}</div>
</div>
```

<figcaption>/source/sass/partials/_foo.sass</figcaption>
```jinja
.foo
  background: grey

.foo__title
  font-weight: bold

.foo__body
  color: red
```

## Syntax

### Keep it flat

Avoid using nesting and the Sass ampersand (`&`) to create BEM structures. This
creates legibility and maintainability issues. A flat structure will be easier
to audit and quickly understand, and avoids indendation mistakes.

<section>
<div>

```sass
.gallery
  ...
.gallery__title
  ...
.gallery__item
  ...
  &--active
    ...
.gallery__item__description
  ...
  &--active
    ...
.gallery__item__footer
  ...
  @at-root [dir=rtl] &
    ...
.gallery__item__author
  ...
```

<do>Do</do>
<label>
  Explicitly describe all BEM structures without abbreviation, and reserve
  the Sass ampersand for modifier classes and <code>@at-root</code> notation.
</label>

</div>
<div>

```sass
.gallery
    ...
  &__title
    ...
  &__item
      ...
    &--active
      ...
    &__description
      ...
        &--active
          ...
    &__footer
      ...
      @at-root [dir=rtl] &
        ...
    &__author
      ...
```
<dont>Don't</dont>
<label>
  BEM syntax should not use indentation to create nested structures.
</label>

</div>

</section>

### Use mixins over extends

Use Sass mixins (`+`) over Sass extends (`%`), including mixins without arguments.
Style sheets created with extends create unnecessary coupling and can introduce
mistakes. Style sheets created with mixins are further encapsulated. Choosing
one also removes the need to make a decision when creating new rules.

## Partial variations

Style variations of a partial intended to be used with `{{partial.class}}`
should be encapsulated and placed at the end of the Sass file, rather that
sprinkling variations throughout the file. This keeps all code related to one
variation in one place, and keeps the rest of the file clean.

All changes created by a variation can be quickly understood, and the variation
can be easily deleted later if it is no longer needed.

<section>
<div>

```sass
.gallery
  ...

.gallery--large
  .gallery__title
    font-size: 1.5em

  .gallery__footer
    font-size: 1.25em

  .gallery__image
    transform: scale(1.5)


```

<do>Do</do>
<label>
Encapsulate all styles for a partial variation at the end of the partial style sheet, in one place.
</label>
</div>
<div>

```sass
.gallery
  ...

.gallery__title
  @at-root .gallery--large &
    font-size: 1.5em

.gallery__footer
  @at-root .gallery--large &
    font-size: 1.25em

.gallery__image
  @at-root .gallery--large &
    transform: scale(1.5)
```

<dont>Don't</dont>
<label>
Sprinkle partial variation styles throughout different rules in the file.
</label>
</div>
</section>

## Element usage

- Use `div` elements for all layout, with proper `aria` and `role` attributes for accessibility.
- Avoid using semantic HTML elements (for non-interactive elements) in site structure.
- Use semantic HTML and styles only for elements within user-supplied (or content manager-supplied) content (such as Markdown or "textarea fields" from a CMS).
- Don't use reset stylesheets.

### Justification

- Using `div` removes the need to guess which HTML element should correctly satisfy a design.
- It also removes the need for a reset stylesheet, and permits default styles for semantic elements to be (correctly) applied to large Markdown blocks or user-supplied content. For example, if a reset stylesheet was used, a content manager could enter a `<b>` tag within a CMS-powered content block and observe no bolded text, and wonder why it's not working.

## Repeated rules and sizes

- Create mixins and variables for repeated rules and sizes.
- Avoid hard-coding sizes and reused values.
