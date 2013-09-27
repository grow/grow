# Grow is in development!

Hello! Grow is still under development and is not quite ready for use. Stay tuned by subscribing to the newsletter on [our website](http://grow.io) or by watching this repository for updates!

# Welcome to Grow!

Grow is almost certainly the best way for teams to build and launch web sites, together. You're reading the documentation for the Python version of Grow (PyGrow), which you can run and use to build web sites wherever you like.

## Two-second terminology

Grow web sites are entirely stored as files, sorted into a particular directory structure. The encapsulation of a Grow web site is called a *pod*. Grow can take a pod and generate an entirely static website (so it can be served by static web servers like Apache, Google Cloud Storage, Amazon S3, GitHub pages, etc.). Or, pods can be deployed to a Grow pod server, where you can take advantage of dynamic serving features.

Pods are dead simple and you can [read more about the structure of a pod](#) if you'd like. Since Grow and Grow.io are backed by Git, pods are best stored as individual Git repositories.

PyGrow comes with handy utilities that can initialize blank (or beautifully-themed!) pods for you, which means you can learn as you go.

## Command rundown

PyGrow's command line utility lets you do things like initialize pods, download pods from Grow.io (or another pod server), or dump an entirely static web site from a pod.

Command | Description
--- | ---
grow dump | Generates static files from a pod and dumps them to a local destination.
grow get | Gets a pod from a remote pod server.
grow init | Initializes a blank (or themed!) pod.
grow run | Starts a local pod server.
grow test | Validates and runs tests for a pod.
grow up | Uploads a pod to a remote pod server.
grow deploy | Deploys a pod to a remote destination.
grow takedown | Takes down a pod from a remote destination.

## Contributing

Since PyGrow must be portable and fully-encapsulated so it can be deployed wherever (such as Google App Engine), this repository uses submodules to include all dependencies that are not part of the Python standard library. In the future, we will make PyGrow available via `pip install` to avoid needing to pull down submodules just for development.

Here's how you can pull down PyGrow and its submodules to contribute:

    # Download Grow and submodules.
    git clone https://github.com/grow/pygrow.git
    cd pygrow && git submodule init && git submodule update && cd ..

    # Initialises a new pod named "testpod".
    # Downloads the "focus" theme from the grow-templates repo.
    ./pygrow/grow/cli.py init focus testpod

    # Start Grow, using the pod you just initialized!
    ./pygrow/grow/cli.py run testpod 

Now that you've got Grow *and* a sample pod on your machine, it's time to start building your site by editing your pod! Pods contain everything you need to build your site: HTML, CSS, JavaScript, images, content, etc. Just edit the files in the "testpod" directory to give it a try.

To add a new page, simply duplicate a file in the `/content/pages/` directory. To add a new post, duplicate a file in `/content/posts/`. You can create a new blueprint (think of blueprints as content types) simply by creating a new directory and corresponding `_blueprint.yaml` file.

## Pod structure

Folder | Description
--- | ---
/content/ | Holds all blueprints and content documents.
/content/&lt;blueprint&gt;/ | Holds all content documents defined by a blueprint.
/content/&lt;blueprint&gt;/_blueprint.yaml | The blueprint for documents in this directory.
/views/ | Holds all views (Jinja2 templates). Each content document can have its own view, or use one defined by a blueprint.
/public/ | Holds all static/media files such as CSS, JavaScript, images.
/pod.yaml | Pod definition file
/tests.yaml | Tests you can write to verify parts of your site.

## Deployment

Unlike other static site generators, Grow comes with deployment built in. Currently, you can deploy your site to another directory on your machine, or to Google Cloud Storage. Upon deployment, Grow maintains an index – so it knows which files to add, modify, and remove.

If you're deploying to Google Cloud Storage, Grow will autoconfigure your GCS bucket for web site serving, and it will check whether your CNAME is setup correctly. Your GCS bucket name should match your domain name. To create a Google Cloud Storage bucket, visit the [Google Cloud Console](https://cloud.google.com/console). You'll also have to verify your domain name before you can create a bucket.

    # Deploy to Google Cloud Storage.
    grow deploy --destination=gcs --bucket<bucket> <pod>
    
    # Deploy to a directory.
    grow deploy --destination=local --out_dir=<directory> <pod>

## Template tags

Tag | Description
--- | ---
{{grow.content}} | A reference to the page's content document.
{{grow.nav(blueprint='&lt;blueprint&gt;')}} | Returns a list of content documents from a specific blueprint.
{{grow.entries(blueprint='&lt;blueprint&gt;', [order_by='&lt;field&gt;',] [reverse=True])}} | Similar to {{grow.nav}}, returns a list of content documents.
