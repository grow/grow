---
$path: /
$view: /views/_base.html

tagline: The best way for teams to build and launch web sites, together.
subtitle: A new open source system for modern, rapid, collaborative web site management and production.
heading: Why you'll love Grow. 
cta:
  title: Try the Grow SDK
  url: /docs/try-grow/
subcta: |
  Interested in Grow in the cloud? <a href="http://grow.io">Check out Grow.io</a>.
callouts:
- title: Your content, unlocked.
  description: Everything is a file. No databases. Backed by Git. Grow is fast and you can use your favorite tools.
- title: No installation, no maintenance.
  description: |
    Focus on what matters: just design and build your sites. Grow runs as a standalone application.
- title: Fully îñtérñåtîøñål.
  description: Reach global visitors with out-of-the-box translation tools. Localization comes included.
- title: Stress-free launches.
  description: Conduct launch review, never miss a file, and always be on time with push-button deployment.
managed:
  heading: Content, design, and collaboration.
  subtitle: |
    Create fully-editable web sites that your whole team can collaborate on: for developers, designers, translators, and writers.
  col1:
    heading: Architect your content.
    title: /content/pages/home.md
    body: |
      ---
      $title: Hello, Grow!
      tagline: Content, design, and collaboration.
      features:
      - Neither cloud, nor local.
      - Fully international.
      - Collaborative editing.
      ---
      # Welcome to Grow!
  col2:
    heading: Apply a design.
    title: /views/home.html
    body: |
      <title>{{g.doc.title}}</title>
      <h1>{{g.doc.tagline}}</h1>
      <ul>
        {% for feature in g.doc.features %}
          <li>{{feature}}
        {% endfor %}
      </ul>
      <main>
        {{g.doc.html|safe}}
      </main>
  col3:
    heading: Unleash it for collaboration.
    title: /views/home.html
    body: |
      Title
      Features
startup:
  heading: Get up and running in seconds.
  instructions: |
    $ pip install grow
    $ grow init mysite https://github.com/growthemes/hello-grow.git
    $ grow run mysite
    # PodServer started -> http://127.0.0.1:8080
---
