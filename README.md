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
    cd pygrow
    git submodule init
    git submodule update

    # Initialize a new pod named "testpod" using the "focus" theme.
    cd ..
    ./pygrow/grow/cli.py init focus testpod
    ./pygrow/grow/cli.py run testpod 
