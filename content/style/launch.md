---
$title: Launch checklist
$order: 6

render: true
enable_sidebar: false

categories:

- title: Performance
  parts:
  - title: Image optimization
  - title: Time to first paint
  - title: Total data transfer size

- title: Analytics and SEO
  parts:
  - title: Social meta tags
  - title: Page titles and descriptions
  - title: Favicon
  - title: Analytics
  - title: Google Search Console
  - title: robots.txt
  - title: Canonical links
  - title: Microdata

- title: Accessibility
  parts:
  - title: Keyboard navigation and element roles
  - title: Alt and title tags
  - title: Contrast ratio

- title: Security
  parts:
  - title: XSS protection
  - title: Google Security Scanner
  - title: Mixed content (HTTPS everywhere)

- title: Dev cleanup
  parts:
  - title: Console logging
  - title: Development/prod-only files

- title: Deployment
  parts:
  - title: Continuous deployment
  - title: Preprocessor deployments
  - title: Monitoring
  - title: Domain
---
<div class="checklist">
  {% for category in doc.categories %}
    <div class="checklist__category">
      <div class="checklist__category__title">{{category.title}}</div>
      <div class="checklist__category__parts">
      {% for part in category.parts %}
        <div class="checklist__category__parts__part">
          {{part.title}}
        </div>
      {% endfor %}
      </div>
    </div>
  {% endfor %}
</div>
